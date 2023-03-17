from knowledgegpt_base.extractors.helpers import check_embedding_extractor
from knowledgegpt_base.utils.utils_subtitles import scrape_youtube
from knowledgegpt_base.utils.utils_embedding import compute_doc_embeddings, compute_doc_embeddings_hf
from knowledgegpt_base.utils.utils_completion import answer_query_with_context


class YTSubsExtractor:
    def __init__(self, video_id: str, model_lang="en", embedding_extractor="hf", is_turbo: bool = False):
        check_embedding_extractor(
            embedding_extractor=embedding_extractor
        )
        self.video_id = video_id
        self.model_lang = model_lang
        self.embedding_extractor = embedding_extractor
        self.max_tokens = 1000
        self.mongo_client = None
        self.df = None
        self.embeddings = None
        self.is_turbo = is_turbo
        self.messages = []
        self.is_first_time = True
        self.answer = ""
        self.prompt = ""

    def extract(self, query: str, max_tokens=1000, to_save: bool = None, mongo_client=None):
        """
        Method that takes a YouTube video ID as input and returns the captions
        as a pandas DataFrame with the key "caption".
        :param video_id: YouTube video ID
        :param query: Query to answer
        :param max_tokens: Maximum number of tokens to use for the prompt
        :param to_save: Whether to save the embeddings to MongoDB
        :return: Tuple of the answer, prompt, and messages
        """
        print("Extracting text...")

        if max_tokens is not None:
            self.max_tokens = max_tokens

        if self.is_first_time:
            if not self.video_id:
                raise ValueError("Video ID is missing")

        if self.df is None:
            self.df = scrape_youtube(self.video_id)

        if self.embeddings is None:
            print("Computing embeddings...")

            if self.embedding_extractor == "hf":
                self.embeddings = compute_doc_embeddings_hf(self.df, self.model_lang)
            else:
                self.embeddings = compute_doc_embeddings(self.df)

            print("Answering query...")

        print("Answering query...")

        self.answer, self.prompt, self.messages = answer_query_with_context(
            query=query,
            df=self.df,
            document_embeddings=self.embeddings,
            embedding_type=self.embedding_extractor,
            model_lang=self.model_lang,
            is_turbo=self.is_turbo,
            messages=self.messages,
            is_first_time=self.is_first_time,
            max_tokens=max_tokens
        )

        if to_save:
            print("Saving to Mongo...")
            self.mongo_client = mongo_client
            self.mongo_client.pair_yt.insert_one({"query": query, "answer": self.answer, "prompt": self.prompt})

        print("Done!")

        return self.answer, self.prompt, self.messages
