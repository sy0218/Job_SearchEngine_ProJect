#!/usr/bin/python3
from kiwipiepy import Kiwi
import spacy

class MorphAnalyzer:
    def __init__(self):
        self._kiwi = Kiwi()
        self._nlp_en = spacy.load("en_core_web_sm", disable=["ner", "parser"])
        self.stopwords = {
            '경우', '사항', '이상', '이후', '통한', '위한', '따른', 
            '사람인', '원티드', '리멤버', '포지션', '합격', '입사', '보상금'
        }

    def analyze(self, text):
        """
        형태소 분석
        - 한국어: 명사(N), 동사(V)만 추출
        - 영어: 명사(NOUN/PROPN), 동사(VERB) 추출 
        - 검색/ES 인덱싱 용도
        """
        if not text:
            return []

        tokens = []
        # 1) 한글만 Kiwi
        kiwi_tokens = self._kiwi.tokenize(text)
        en_words = []

        for t in kiwi_tokens:
            if t.tag.startswith("N"):
                if t.form not in self.stopwords and len(t.form) > 1:
                    tokens.append(t.form)
            elif t.tag.startswith("V") and t.tag not in ("VCP", "VCN"):
                if t.lemma not in self.stopwords and len(t.lemma) > 1:
                    tokens.append(t.lemma)
            elif t.tag == "SL":
                en_words.append(t.form.lower())

        if en_words:
            en_text = " ".join(en_words)
            en_doc = self._nlp_en(en_text)
            for et in en_doc:
                if et.pos_ in ["NOUN", "PROPN", "VERB"] and len(et.text) > 1:
                    tokens.append(et.lemma_)

        return list(set(tokens))
