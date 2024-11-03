from typing import Iterator

from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

from share import llm, supported_langs


def getRawCodeStream(user_requirement: str, code_structure: str, filename: str, language: str) -> Iterator[str]:
    """通过用户需求、代码结构、语言、文件名，生成大模型回答的原始字符流"""

    language = language.lower()
    if language not in supported_langs:
        raise ValueError(f"Unsupported language: {language}. (Support: {supported_langs})")

    template = f"""
        请根据以下信息，为指定文件生成基本 {language} 代码。
        用户需求：{user_requirement}
        代码框架：
        ```markdown
        {code_structure}
        ```
        需要生成的文件：{filename}。
        回答：
    """
    prompt = ChatPromptTemplate.from_template(template)
    llm_chain = (
        prompt |
        llm |
        StrOutputParser()
    )
    return llm_chain.stream({})