from django.db import transaction

from elearning.models import (
    Answer,
    Course,
    CourseEnrollment,
    Lesson,
    LessonEnrollment,
    Question,
    UserAnswer
)


class TestReview:
    def __init__(self, user_id, lesson_id, user_questions=[]):
        self._user_id = user_id
        self._lesson_id = lesson_id
        self._user_questions = user_questions
        self._course_id = None

        self.__correct_answers = {}
        self.__user_answers = {}

    def evaluate(self):
        try:
            self.__check_integrity()

            is_approved = self.__evaluate()

            return is_approved, ""

        except Exception as ex:
            return False, ex

    def __evaluate(self):
        score = self.__get_score()

        lesson = Lesson.objects.get(pk=self._lesson_id)

        self._course_id = lesson.course_id

        if score >= lesson.approval_score:
            self.__save_answers(score)

            return True

        return False

    def __get_score(self):
        self.__process_input_information()

        accumulated_score = 0

        for key in self.__correct_answers.keys():
            question_type = self.__correct_answers[key]['type']
            score = self.__correct_answers[key]['score']
            correct_answers = self.__correct_answers[key]['answers']
            user_answers = self.__user_answers[key]['answers']

            is_correct = self.__evaluate_answers(
                question_type,
                correct_answers,
                user_answers
            )

            if is_correct:
                accumulated_score += score

        return accumulated_score
    
    def __process_input_information(self):
        self.__get_correct_answers()
        self.__proccess_user_questions()

    def __evaluate_answers(self, question_type, correct_answers=[], user_answers=[]):

        if question_type == "BOOLEAN" or question_type == "MULTIPLE_CHOOSE_A_CORRECT_ONE":
            for user_answer in user_answers:
                if user_answer in correct_answers:
                    return True

        if question_type == "CHOOSE_ALL_THE_RIGHT":
            if len(correct_answers) == len(user_answers):
                total = 0
                for user_answer in user_answers:
                    if user_answer in correct_answers:
                        total += 1

                if(total == len(correct_answers)):
                    return True

        return False

    def __get_correct_answers(self):
        answers = Answer.objects.is_correct().by_lesson(
            self._lesson_id
        ).select_related('question')

        for answer in answers:
            key = str(answer.question_id)

            if key not in self.__correct_answers:
                self.__correct_answers[key] = {}
                self.__correct_answers[key]['type'] = answer.question.question_type
                self.__correct_answers[key]['score'] = answer.question.score
                self.__correct_answers[key]['answers'] = []

            self.__correct_answers[key]['answers'].append(answer.id)

    def __proccess_user_questions(self):
        for question in self._user_questions:
            key = str(question['id'])

            if key not in self.__user_answers:
                self.__user_answers[key] = {}
                self.__user_answers[key]['answers'] = []

            for answer in question['answers']:
                self.__user_answers[key]['answers'].append(answer['id'])

    def __check_integrity(self):
        try:
            questions = Question.objects.by_lesson(self._lesson_id)

            questions_ids = [question.id for question in questions]
            questions_user_ids = [question['id']
                                  for question in self._user_questions]

            message = ""

            for question_id in questions_ids:
                if question_id not in questions_user_ids:
                    question = Question.objects.get(pk=question_id)
                    message = message + f"question \"{question.description}\" was not answered \n"
            
            if message != "":
                raise Exception(message)

        except Exception as ex:
            raise Exception(ex)

    def __save_answers(self, score):
        with transaction.atomic():
            for key in self.__user_answers.keys():
                for answer in self.__user_answers[key]['answers']:
                    UserAnswer.objects.create(
                        user_id=self._user_id,
                        answer_id=answer
                    )

            lesson = LessonEnrollment.objects.get(
                lesson_id=self._lesson_id,
                user_id=self._user_id
            )

            lesson.score = score
            lesson.is_approved = True
            lesson.save()

            self._check_approved_course()

    def _check_approved_course(self):
        total_lessons = Lesson.objects.by_course(self._course_id).count()

        total_lessons_approved = LessonEnrollment.objects.by_course(
            self._course_id
        ).by_user(self._user_id).is_approved().count()

        if total_lessons == total_lessons_approved:
            course_enrollment = CourseEnrollment.objects.get(
                user_id=self._user_id,
                pk=self._course_id
            )

            course_enrollment.is_approved = True
            course_enrollment.save()
