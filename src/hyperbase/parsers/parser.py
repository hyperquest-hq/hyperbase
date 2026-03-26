from typing import List


class Parser:
    def sentensize(self, text):
        raise NotImplementedError

    def parse(self, text):
        for sentence in self.sentensize(text):
            for parse in self.parse_sentence(sentence):
                yield parse

    def parse_sentence(self, sentence):
        raise NotImplementedError

    def parse_batch(self, sentences: List[str]) -> List[List[dict]]:
        """Parse multiple sentences. Subclasses may override with a
        true batched implementation (e.g. a single CT2 call)."""
        return [self.parse_sentence(sentence) for sentence in sentences]

    def parse_text(
        self, text: str, batch_size: int = 8, progress: bool = False
    ) -> List[dict]:
        """Sentensize text, then parse all sentences in batches.

        Returns a flat list of parse results across all sentences.
        """
        sentences = [s for s in self.sentensize(text) if len(s.split()) > 1]
        batch_range = range(0, len(sentences), batch_size)
        if progress:
            from tqdm import tqdm
            batch_range = tqdm(batch_range, desc="Parsing batches", leave=False)
        results: List[dict] = []
        for i in batch_range:
            batch = sentences[i:i + batch_size]
            for sentence_results in self.parse_batch(batch):
                results.extend(sentence_results)
        return results
