from rest_framework import serializers

from .models import AiRecommendation, DiaryEntry, Genre, Movie


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']


class MovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    genre_ids = serializers.PrimaryKeyRelatedField(
        source='genres', queryset=Genre.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Movie
        fields = ['id', 'title', 'year', 'description', 'poster_url', 'genres', 'genre_ids']

    def validate_year(self, value):
        if not 1888 <= value <= 2100:
            raise serializers.ValidationError('Год должен быть от 1888 до 2100.')
        return value


class DiaryEntrySerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)
    movie_id = serializers.PrimaryKeyRelatedField(source='movie', queryset=Movie.objects.all(), write_only=True)

    class Meta:
        model = DiaryEntry
        fields = ['id', 'movie', 'movie_id', 'status', 'rating', 'review', 'watched_at', 'created_at']
        read_only_fields = ['created_at']

    def validate_rating(self, value):
        if value is not None and not 1 <= value <= 10:
            raise serializers.ValidationError('Оценка должна быть от 1 до 10.')
        return value

    def validate_review(self, value):
        value = value.strip()
        if len(value) > 2000:
            raise serializers.ValidationError('Отзыв слишком длинный (максимум 2000 символов).')
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        movie = attrs.get('movie')
        if movie and self.instance is None and DiaryEntry.objects.filter(user=user, movie=movie).exists():
            raise serializers.ValidationError('Этот фильм уже есть в вашем дневнике.')
        status = attrs.get('status', getattr(self.instance, 'status', DiaryEntry.STATUS_WANT))
        if status == DiaryEntry.STATUS_WANT and attrs.get('rating'):
            raise serializers.ValidationError('Оценку можно поставить только просмотренному фильму.')
        return attrs


class AiRequestSerializer(serializers.Serializer):
    mood = serializers.CharField(max_length=100, min_length=2, trim_whitespace=True)


class AiRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiRecommendation
        fields = ['id', 'mood', 'response_text', 'created_at']
