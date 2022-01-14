import pickle
from typing import List, Dict

from presidio_evaluator import InputSample
from presidio_evaluator.models import BaseModel


class CRFModel(BaseModel):
    def __init__(
        self,
        model_pickle_path: str = "../models/crf.pickle",
        entities_to_keep: List[str] = None,
        verbose: bool = False,
        entity_mapping: Dict[str, str] = None,
    ):
        super().__init__(
            entities_to_keep=entities_to_keep,
            verbose=verbose,
            entity_mapping=entity_mapping
        )

        if model_pickle_path is None:
            raise ValueError("model_pickle_path must be supplied")

        with open(model_pickle_path, "rb") as f:
            self.model = pickle.load(f)

    def predict(self, sample: InputSample) -> List[str]:
        tags = CRFModel.crf_predict(sample, self.model)

        if len(tags) != len(sample.tokens):
            print("mismatch between previous tokens and new tokens")
        return tags

    @staticmethod
    def crf_predict(sample, model):
        sample.translate_input_sample_tags()

        conll = sample.to_conll(translate_tags=True)
        sentence = [(di["text"], di["pos"], di["label"]) for di in conll]
        features = CRFModel.sent2features(sentence)
        return model.predict([features])[0]

    @staticmethod
    def word2features(sent, i):
        word = sent[i][0]
        postag = sent[i][1]

        features = {
            "bias": 1.0,
            "word.lower()": word.lower(),
            "word[-3:]": word[-3:],
            "word[-2:]": word[-2:],
            "word.isupper()": word.isupper(),
            "word.istitle()": word.istitle(),
            "word.isdigit()": word.isdigit(),
            "postag": postag,
            "postag[:2]": postag[:2],
        }
        if i > 0:
            word1 = sent[i - 1][0]
            postag1 = sent[i - 1][1]
            features.update(
                {
                    "-1:word.lower()": word1.lower(),
                    "-1:word.istitle()": word1.istitle(),
                    "-1:word.isupper()": word1.isupper(),
                    "-1:postag": postag1,
                    "-1:postag[:2]": postag1[:2],
                }
            )
        else:
            features["BOS"] = True

        if i < len(sent) - 1:
            word1 = sent[i + 1][0]
            postag1 = sent[i + 1][1]
            features.update(
                {
                    "+1:word.lower()": word1.lower(),
                    "+1:word.istitle()": word1.istitle(),
                    "+1:word.isupper()": word1.isupper(),
                    "+1:postag": postag1,
                    "+1:postag[:2]": postag1[:2],
                }
            )
        else:
            features["EOS"] = True

        return features

    @staticmethod
    def sent2features(sent):
        return [CRFModel.word2features(sent, i) for i in range(len(sent))]

    @staticmethod
    def sent2labels(sent):
        return [label for token, postag, label in sent]

    @staticmethod
    def sent2tokens(sent):
        return [token for token, postag, label in sent]
