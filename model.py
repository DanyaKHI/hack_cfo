import numpy as np
from enum import Enum
import joblib

from consts import PATH_SVM, PATH_CATBOOST, PATH_CATS, PATH_LOGREG, M_CATEGORIES, CATERS, U_CATERS, N_CATEGORIES, conf_thershold


class ModelFeedbackType(Enum):
    end_point = 0
    continue_point = 1
    no_class_point = 2


class ModelFeedback:
    """
    Class of feedback model
    """
    feedback_type: ModelFeedbackType
    data: str

    def __init__(self, feedback_type: ModelFeedbackType, data: str):
        self.feedback_type = feedback_type
        self.data = data


class ThemeModel:
    """
    QA model
    """
    def __init__(self):
        self.ppl_boost = joblib.load(PATH_CATBOOST)
        self.ppl_logreg = joblib.load(PATH_LOGREG)
        self.ppl_svm = joblib.load(PATH_SVM)

        self.models_cats = {}
        for cat in M_CATEGORIES:
            self.models_cats[cat] = joblib.load(f'{PATH_CATS}/{cat}.joblib')

    async def __inference_classifier(self, request: str) -> np.ndarray:
        y_pred_boost = self.ppl_boost.predict([request])[0][0]
        y_pred_logreg = self.ppl_logreg.predict([request])[0]
        y_pred_svm = self.ppl_svm.predict([request])[0]

        anses = []
        anses.append(CATERS[y_pred_boost])
        anses.append(CATERS[y_pred_logreg])
        anses.append(CATERS[y_pred_svm])

        anses = sorted(anses)
        if anses[0] == anses[-1]:
            y_pred_ansamble = U_CATERS[anses[0]]
        elif anses[0] == anses[1]:
            y_pred_ansamble = U_CATERS[anses[0]]
        elif anses[1] == anses[2]:
            y_pred_ansamble = U_CATERS[anses[1]]
        else:
            y_pred_ansamble = y_pred_logreg

        if y_pred_ansamble in M_CATEGORIES:
            cur_pred = self.models_cats[y_pred_ansamble].predict([request])[0]
            probs = self.models_cats[y_pred_ansamble].predict_proba([request])
            if probs.max() < conf_thershold:
                return (0, cur_pred)
            return (1, cur_pred)
        else:
            return (1, N_CATEGORIES[y_pred_ansamble])

    async def inference(self, requests: list) -> ModelFeedback:
        """
        :param requests: передается список сообщений
        :return: результат модели классификации
        """
        is_valid, predict = await self.__inference_classifier(" ".join(requests))
        if is_valid:
            return ModelFeedback(feedback_type=ModelFeedbackType.end_point,
                                 data=predict)
        else:
            return ModelFeedback(feedback_type=ModelFeedbackType.no_class_point,
                                 data=predict)

    async def __call__(self, request: list) -> ModelFeedback:
        return await self.inference(request)





