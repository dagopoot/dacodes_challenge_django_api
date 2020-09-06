from django.db import transaction
from rest_framework import serializers

from .models import (
    Answer,
    Course,
    CourseEnrollment,
    Lesson,
    LessonEnrollment,
    Question,
    UserAnswer
)


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = (
            'id',
            'name',
            'dependent',
        )


class CourseAvailableSerializer(serializers.ModelSerializer):
    is_approved = serializers.BooleanField()
    dependent_is_approved = serializers.BooleanField()
    is_subscribed = serializers.BooleanField()

    class Meta:
        model = Course
        fields = (
            'id',
            'name',
            'dependent',
            'is_subscribed',
            'is_approved',
            'dependent_is_approved',
        )


class LessonsAvailableSerializer(serializers.ModelSerializer):
    is_approved = serializers.BooleanField()
    dependent_is_approved = serializers.BooleanField()

    class Meta:
        model = Lesson
        fields = (
            'id',
            'title',
            'description',
            'approval_score',
            'dependent',
            'course',
            'is_approved',
            'dependent_is_approved',
        )


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = (
            'id',
            'title',
            'description',
            'approval_score',
            'dependent',
            'course',
        )


class LessonPreviewSerializer(serializers.ModelSerializer):
    is_approved = serializers.BooleanField()
    dependent_is_approved = serializers.BooleanField()

    class Meta:
        model = Lesson
        fields = (
            'id',
            'title',
            'course',
            'is_approved',
            'dependent_is_approved',
        )


class AnswerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Answer
        fields = (
            'id',
            'description',
            'is_correct',
        )


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = Question
        fields = (
            'id',
            'description',
            'score',
            'question_type',
            'lesson',
            'answers',
        )

    def create(self, validated_data):
        with transaction.atomic():
            answers = validated_data.pop('answers')
            question = Question.objects.create(**validated_data)

            for answer in answers:
                Answer.objects.create(question=question, **answer)

            return question

    def update(self, instance, validated_data):
        with transaction.atomic():
            answers = validated_data.pop('answers')

            instance.description = validated_data.get(
                'description',
                instance.description
            )
            instance.score = validated_data.get('score', instance.score)
            instance.question_type = validated_data.get(
                'question_type',
                instance.question_type
            )
            instance.lesson = validated_data.get('lesson', instance.lesson)
            instance.save()

            previous_answers = Answer.objects.filter(question_id=instance.id)
            previous_answers_ids = [answer.id for answer in previous_answers]

            for answer in answers:
                if 'id' in answer:
                    answer_update = Answer.objects.get(pk=answer['id'])
                    answer_update.description = answer['description']
                    answer_update.is_correct = answer['is_correct']
                    answer_update.save()

                    previous_answers_ids.remove(answer['id'])
                else:
                    Answer.objects.create(question=instance, **answer)

            if len(previous_answers_ids) > 0:
                Answer.objects.filter(pk__in=previous_answers_ids).delete()

            return instance

    def validate(self, data):
        """
        check that the answers are as expected
        """
        if len(data['answers']) < 2:
            raise serializers.ValidationError(
                "At least two possible answers are required")

        corrects = 0

        for answer in data['answers']:
            if answer['is_correct'] == True:
                corrects += 1

        if corrects == 0:
            raise serializers.ValidationError(
                "At least one correct answer was expected")

        if data['question_type'] == "BOOLEAN":
            if len(data['answers']) != 2:
                raise serializers.ValidationError(
                    "Two responses were expected")

        return data


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course = CourseSerializer()

    class Meta:
        model = CourseEnrollment
        fields = (
            'id',
            'user',
            'course',
        )


class LessonEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonEnrollment
        fields = (
            'id',
            'user',
            'lesson',
        )


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = (
            'id',
            'user',
            'answer',
        )


class TestLessonSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)


class EmptySerializer(serializers.Serializer):
    pass


class GetAnswerForTestSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Answer
        fields = (
            'id',
            'description',
        )


class GetLessonQuestionSerializer(serializers.ModelSerializer):
    answers = GetAnswerForTestSerializer(many=True)

    class Meta:
        model = Question
        fields = (
            'id',
            'description',
            'question_type',
            'lesson',
            'answers',
        )


class SendAnswersSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Answer
        fields = (
            'id',
        )


class SendQuestionsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    answers = SendAnswersSerializer(many=True, required=True)

    class Meta:
        model = Question
        fields = (
            'id',
            'answers',
        )


class SendTestSerializer(serializers.Serializer):
    questions = SendQuestionsSerializer(many=True)

    def validate(self, data):
        if len(data['questions']) == 0:
            raise serializers.ValidationError({
                'questions': "At least one question"
            })

        for question in data['questions']:
            if len(question['answers']) == 0:
                raise serializers.ValidationError({
                    'questions': f"Question {question['description']} requires an answer"
                })

        return data


class LogicSerializer(serializers.Serializer):
    N = serializers.IntegerField(required=True, min_value=1)
    M = serializers.IntegerField(required=True, min_value=1)

