
import os
from langchain_community.document_loaders import TextLoader, UnstructuredPDFLoader, UnstructuredWordDocumentLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.tools import tool

class FileQASystem:
    def __init__(self, file_path):
        self.file_path = file_path
        self.documents = self.load_documents(file_path)
        self.vector_store = self.build_vector_store(self.documents)
        self.llm = ChatOpenAI(temperature=0.0)
        self.qa = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(),
            return_source_documents=True
        )

    @staticmethod
    def load_documents(file_path):
        SUPPORTED_EXTS = [".txt", ".pdf", ".docx", ".md"]
        LOADER_MAP = {
            ".txt": TextLoader,
            ".pdf": UnstructuredPDFLoader,
            ".docx": UnstructuredWordDocumentLoader,
            ".md": UnstructuredMarkdownLoader,
        }
        ext = os.path.splitext(file_path)[-1].lower()
        if ext not in SUPPORTED_EXTS:
            raise ValueError(f"暂不支持的文件类型: {ext}")
        loader_cls = LOADER_MAP[ext]
        loader = loader_cls(file_path)
        return loader.load()

    @staticmethod
    def build_vector_store(documents):
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        texts = text_splitter.split_documents(documents)
        embeddings = OpenAIEmbeddings()
        return FAISS.from_documents(texts, embeddings)

    def ask(self, query):
        result = self.qa({"query": query})
        answer = result["result"]
        sources = result.get("source_documents", [])
        return answer, sources

# 下面保留get_fileqa_tool函数不变

def get_fileqa_tool(llm):
    file_qa_cache = {}
    
    @tool
    def fileqa_tool(input_str: str) -> str:
        """文件问答工具，用于处理文档相关问题。输入格式：'<文件路径>|<问题>'"""
        try:
            print(f"fileqa_tool被调用，输入: {input_str}")
            
            if "|" not in input_str:
                return "file_qa 代理输入格式错误，应为 '<文件路径>|<问题>'"
            
            file_path, query = input_str.split("|", 1)
            file_path = file_path.strip()
            query = query.strip()
            
            print(f"解析文件路径: {file_path}")
            print(f"解析查询问题: {query}")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return f"文件不存在: {file_path}"
            
            cache_key = (file_path, )
            if cache_key not in file_qa_cache:
                try:
                    print(f"开始加载文件: {file_path}")
                    file_qa_cache[cache_key] = FileQASystem(file_path)
                    print(f"文件加载成功: {file_path}")
                except Exception as e:
                    error_msg = f"文件加载失败 ({file_path}): {str(e)}"
                    print(f"❌ {error_msg}")
                    return error_msg
            
            file_qa = file_qa_cache[cache_key]
            print(f"开始问答处理...")
            answer, sources = file_qa.ask(query)
            
            # 构建结果
            result = f"文件内容分析结果:\n\n{answer}"
            if sources:
                result += f"\n\n来源信息:"
                for i, doc in enumerate(sources[:3], 1):
                    source = getattr(doc.metadata, 'source', '未知')
                    result += f"\n{i}. {source}"
            
            print(f"问答处理完成，结果长度: {len(result)}")
            return result
            
        except Exception as e:
            error_msg = f"fileqa_tool执行失败: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    return fileqa_tool