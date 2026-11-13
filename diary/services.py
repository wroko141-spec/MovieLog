"""Подбор фильмов с помощью ИИ."""
import json
import logging
import urllib.request
from collections import Counter

from django.conf import settings

from .models import AiRecommendation, DiaryEntry, Movie

log = logging.getLogger(__name__)

# слова в настроении -> подходящие жанры (для встроенного подбора)
MOOD_GENRES = {
    'смеш': ['Комедия'], 'весел': ['Комедия', 'Мультфильм'], 'посмеят': ['Комедия'],
    'добр': ['Мультфильм', 'Комедия', 'Драма'], 'уют': ['Мультфильм', 'Мелодрама'],
    'груст': ['Драма'], 'поплак': ['Драма'], 'задум': ['Драма', 'Фантастика'],
    'страш': ['Ужасы', 'Триллер'], 'напряж': ['Триллер'], 'нерв': ['Триллер'],
    'космос': ['Фантастика'], 'фантаст': ['Фантастика'], 'будущ': ['Фантастика'],
    'любов': ['Мелодрама'], 'романт': ['Мелодрама'], 'свидан': ['Мелодрама', 'Комедия'],
    'приключ': ['Приключения'], 'путешеств': ['Приключения'], 'экшен': ['Боевик'],
    'драйв': ['Боевик'], 'адренал': ['Боевик', 'Триллер'],
    'семь': ['Мультфильм', 'Приключения'], 'дет': ['Мультфильм'],
}


class AiService:
    def __init__(self):
        self.api_url = settings.AI_API_URL
        self.api_key = settings.AI_API_KEY
        self.model = settings.AI_MODEL

    def recommend(self, user, mood):
        entries = list(DiaryEntry.objects.filter(user=user).select_related('movie'))
        seen_ids = {e.movie_id for e in entries}
        candidates = list(Movie.objects.exclude(id__in=seen_ids).prefetch_related('genres'))
        prompt = self.build_prompt(entries, candidates, mood)

        text = None
        if self.api_url and self.api_key:
            try:
                text = self.ask_llm(prompt)
            except Exception as exc:  # сеть, ключ, лимит - работаем дальше без ИИ
                log.warning('AI request failed: %s', exc)
        if not text:
            text = self.local_recommend(entries, candidates, mood)

        return AiRecommendation.objects.create(user=user, mood=mood, request_text=prompt, response_text=text)

    @staticmethod
    def build_prompt(entries, candidates, mood):
        watched = [f'{e.movie.title} ({e.movie.year}) - оценка {e.rating}' for e in entries
                   if e.status == DiaryEntry.STATUS_WATCHED and e.rating]
        catalog = [f'{m.title} ({m.year}), жанры: {", ".join(g.name for g in m.genres.all())}' for m in candidates[:60]]
        return (
            'Ты помощник сайта MovieLog. Посоветуй пользователю 3 фильма из каталога под его настроение. '
            'Учитывай, какие фильмы он уже оценил. Отвечай по-русски, коротко: название, год и одна фраза, '
            'почему подходит. Советуй только фильмы из каталога.\n'
            f'Настроение: {mood}\n'
            f'Уже посмотрел: {"; ".join(watched) or "пока ничего"}\n'
            f'Каталог: {"; ".join(catalog)}'
        )

    def ask_llm(self, prompt):
        body = json.dumps({
            'model': self.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 500,
            'temperature': 0.7,
        }).encode('utf-8')
        req = urllib.request.Request(
            self.api_url, data=body, method='POST',
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.api_key}'},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        return data['choices'][0]['message']['content'].strip()

    @staticmethod
    def local_recommend(entries, candidates, mood):
        """Подбор без внешнего ИИ: жанры по словам из настроения + любимые жанры пользователя."""
        mood_l = mood.lower()
        wanted = Counter()
        for key, genres in MOOD_GENRES.items():
            if key in mood_l:
                for g in genres:
                    wanted[g] += 3
        for e in entries:
            if e.rating and e.rating >= 8:
                for g in e.movie.genres.all():
                    wanted[g.name] += 1
        if not candidates:
            return 'Вы уже добавили в дневник все фильмы из каталога. Скоро администратор добавит новые!'

        def score(m):
            return sum(wanted[g.name] for g in m.genres.all())

        best = sorted(candidates, key=lambda m: (score(m), m.year), reverse=True)[:3]
        lines = [f'Под настроение «{mood}» советую:']
        for i, m in enumerate(best, 1):
            genres = ', '.join(g.name for g in m.genres.all())
            lines.append(f'{i}. {m.title} ({m.year}) - {genres}.')
        if not any(score(m) for m in best):
            lines.append('Точного совпадения по настроению не нашлось, поэтому это свежие фильмы из каталога.')
        return '\n'.join(lines)
