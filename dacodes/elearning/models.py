from django.db import models
from django.conf import settings

from django.db.models.query import QuerySet

from core.models import TimeStampedModel
from .settings import QUESTION_TYPES


class CourseManager(models.Manager):
    def can_subscribe(self, course_id, user_id):
        try:
            course = Course.objects.get(pk=course_id)

            if self.is_subscribed(course_id, user_id):
                return False

            if course.dependent is None:
                return True

            if self.is_approved(course.dependent.id, user_id):
                return True

        except Exception as ex:

            return False

    def is_subscribed(self, course_id, user_id):
        course_enrollment = CourseEnrollment.objects.filter(
            course_id=course_id, user_id=user_id)

        if course_enrollment.exists():
            return True

        return False

    def subscribe(self, course_id, user_id):
        if not Course.objects.is_subscribed(course_id, user_id):
            if Course.objects.can_subscribe(course_id, user_id):
                CourseEnrollment.objects.create(
                    course_id=course_id, user_id=user_id)
                return True
        else:
            return True

        return False

    def is_available_for_user(self, course_id, user_id):
        try:
            course = Course.objects.get(pk=course_id)

            if course.dependent is None:
                return True

            if self.is_approved(course.dependent.id, user_id):
                return True

            if self.is_approved(course.id, user_id):
                return True

        except Exception as ex:
            return False

        return False

    def is_approved(self, course_id, user_id):
        course_enrollment = CourseEnrollment.objects.filter(
            course_id=course_id, user_id=user_id)

        if course_enrollment.exists():
            if course_enrollment[0].is_approved:
                return True

        return False


class Course(TimeStampedModel):
    name = models.CharField(max_length=200)
    dependent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        related_name="predecessor_course"
    )

    objects = CourseManager()

    def __str__(self):
        return self.name


class LessonQuerySet(QuerySet):
    def by_course(self, course_id):
        return self.filter(course_id=course_id)


class LessonManager(models.Manager):
    def get_queryset(self):
        return LessonQuerySet(self.model, using=self._db)

    def by_course(self, course_id):
        return self.get_queryset().by_course(course_id)

    def can_subscribe(self, lesson_id, user_id):
        try:
            lesson = Lesson.objects.get(pk=lesson_id)

            if self.is_subscribed(lesson_id, user_id):
                return False

            if lesson.dependent is None:
                if lesson.course.dependent_id is None:
                    return True

                if Course.objects.is_approved(lesson.course.dependent_id, user_id):
                    return True

            if self.is_approved(lesson.dependent.id, user_id):
                return True

        except Exception as ex:

            return False

    def is_subscribed(self, lesson_id, user_id):
        lesson_enrollment = LessonEnrollment.objects.filter(
            lesson_id=lesson_id, user_id=user_id)

        if lesson_enrollment.exists():
            return True

        return False

    def subscribe(self, lesson_id, user_id):
        if not Lesson.objects.is_subscribed(lesson_id, user_id):
            if Lesson.objects.can_subscribe(lesson_id, user_id):
                LessonEnrollment.objects.create(
                    lesson_id=lesson_id, user_id=user_id)
                return True
        else:
            return True

        return False

    def is_available_for_user(self, lesson_id, user_id):
        try:
            lesson = Lesson.objects.get(pk=lesson_id)

            if lesson.dependent is None:
                return True

            if self.is_approved(lesson.dependent.id, user_id):
                return True

            if self.is_approved(lesson.id, user_id):
                return True

        except Exception as ex:
            return False

        return False

    def is_approved(self, lesson_id, user_id):
        lesson_enrollment = LessonEnrollment.objects.filter(
            lesson_id=lesson_id, user_id=user_id)

        if lesson_enrollment.exists():
            if lesson_enrollment[0].is_approved:
                return True

        return False


class Lesson(TimeStampedModel):
    course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        related_name="lessons"
    )
    dependent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        related_name="predecessor_lesson"
    )
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    approval_score = models.IntegerField()

    objects = LessonManager()

    def __str__(self):
        return self.title


class QuestionQuerySet(QuerySet):
    def by_lesson(self, lesson_id):
        return self.filter(lesson_id=lesson_id)


class QuestionManager(models.Manager):
    def get_queryset(self):
        return QuestionQuerySet(self.model, using=self._db)

    def by_lesson(self, lesson_id):
        return self.get_queryset().by_lesson(lesson_id)


class Question(TimeStampedModel):
    lesson = models.ForeignKey(
        'Lesson',
        on_delete=models.CASCADE,
        related_name="question"
    )
    description = models.CharField(max_length=200)
    score = models.IntegerField()
    question_type = models.CharField(
        max_length=200,
        choices=QUESTION_TYPES,
        default='MULTIPLE_CHOOSE_A_CORRECT_ONE'
    )

    objects = QuestionManager()

    def __str__(self):
        return self.description


class AnswerQuerySet(QuerySet):
    def by_question(self, question_id):
        return self.filter(question_id=question_id)

    def is_correct(self):
        return self.filter(is_correct=True)

    def by_lesson(self, lesson_id):
        return self.filter(question__lesson_id=lesson_id)


class AnswerManager(models.Manager):
    def get_queryset(self):
        return AnswerQuerySet(self.model, using=self._db)

    def by_question(self, question_id):
        return self.get_queryset().by_question(question_id)

    def is_correct(self):
        return self.get_queryset().is_correct()

    def by_lesson(self, lesson_id):
        return self.get_queryset().by_lesson(lesson_id)


class Answer(TimeStampedModel):
    question = models.ForeignKey(
        'Question',
        on_delete=models.CASCADE,
        related_name="answers"
    )
    description = models.CharField(max_length=200)
    is_correct = models.BooleanField()

    objects = AnswerManager()

    def __str__(self):
        return self.description


class CourseEnrollment(TimeStampedModel):
    course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    is_approved = models.BooleanField(default=False)


class LessonEnrollmentQuerySet(QuerySet):
    def by_course(self, course_id):
        return self.filter(lesson__course_id=course_id)

    def is_approved(self):
        return self.filter(is_approved=True)

    def by_user(self, user_id):
        return self.filter(user_id=user_id)


class LessonEnrollmentManager(models.Manager):
    def get_queryset(self):
        return LessonEnrollmentQuerySet(self.model, using=self._db)

    def by_course(self, course_id):
        return self.get_queryset().by_course(course_id)

    def is_approved(self):
        return self.get_queryset().is_approved()

    def by_user(self, user_id):
        return self.get_queryset().by_user(user_id)


class LessonEnrollment(TimeStampedModel):
    lesson = models.ForeignKey(
        'Lesson',
        on_delete=models.CASCADE,
        related_name="enrollments"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lessons'
    )
    is_approved = models.BooleanField(default=False)
    score = models.IntegerField(default=0)

    objects = LessonEnrollmentManager()


class UserAnswer(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    answer = models.ForeignKey(
        'Answer',
        on_delete=models.CASCADE,
        related_name="answered"
    )
