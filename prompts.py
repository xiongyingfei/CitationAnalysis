long_system = """用户将提供给你一段某篇论文（称为“引用论文”）中的待分析文本和另一篇论文（称为“被引论文”）的信息，请从文本中提取引用被引论文的句子，并分析这些句子是否正面评价了被引论文。接下来用一个例子说明什么样的句子引用了被引论文，什么样的句子对被引论文进行了正面评价。

## 示例被引论文信息
* 论文信息：Yican Sun, Xuanyu Peng, Yingfei Xiong*. Synthesizing Efficient Memoization Algorithms. OOPSLA'23: Object-Oriented Programming, Systems, Languages and Applications, October 2023.
* 引用编号：[20]
* 方法名称：SynMem

## 句子是否应该提取示例
Program Synthesis for complex algorithms is an important research problem [1, 18, 25]. -> 不应该提取，没有引用。
Program Synthesis for complex algorithms is an important research problem [1, 18-25]. -> 应该提取，通过编号范围引用。
Program Synthesis for complex algorithms is an important research problem [20]. -> 应该提取，通过编号引用。
The newest approach is proposed by Sun et al. (2023). -> 应该提取，通过作者引用。
The newest approach is proposed by (Sun, Peng, and Xiong, 2023). -> 应该提取，通过作者引用。
SynMem is evaluated on a set of benchmarks. -> 应该提取，通过方法名称引用。
Yican Sun, Xuanyu Peng, Yingfei Xiong*. Synthesizing Efficient Memoization Algorithms. OOPSLA'23: Object-Oriented Programming, Systems, Languages and Applications, October 2023. -> 不应该提取，只是参考文献，并非引用句子。注意参考文献不应该提取，也不是正面评价。

## 句子是否是正面引用示例。
正面引用包括称赞被引论文，比如称赞被引论文新颖、首次尝试了某种方向、效果突出等；或者深入参考被引论文内容，比如应用被引论文方法去解决新问题、基于被引论文方法构建新方法等，或者在新领域验证被引论文工作，发现论文工作表现突出等。
句子：SynMem [20] is a recent technique that significantly improves the performance of synthesizing memoization algorithms, based on a combination of inductive methods and deductive methods.
分析：称赞SynMem显著提升了（significantly improves）合成记忆化算法的性能。
正面评价：True

句子：Sun et al. proposed a novel approach.
分析：评论被引论文提出了一种“新颖（novel）”的方法。
正面评价：True

句子：Since the eventual goal of our study is to assess the reliability of author and automated annotations, we need a set of problems that have been labeled before by tool authors and can be used as input to automated test case generation tools designed for program repair. We find the datasets recently released by Sun et al. [20], Martinez et al. [23], and Le et al. [21] to be suitable.
分析：基于[20]的数据集设计了补丁验证可靠性实验。
正面评价：True

句子：we implemented it atop the SynMem [20] program synthesis system. We picked SynMem because it is a state-of-the-art approach for memoization algorithms.
分析：在SynMem的基础上设计了实验，并称赞SynMem是目前效果最好（state-of-the-art）的记忆化算法合成方法。
正面评价：True

句子：There are a lot of existing work for program synthesis [1, 11, 20-25, 35].</Text>
分析：只是作为大量已有工作中的一个进行列举，并没有正面评价或者深入参考被引论文内容。
正面评价：False

## 输入输出示例
待分析文本：Program Synthesis for complex algorithms is an important research problem [1, 18, 25]. There are a lot of existing approaches to this problem in recent years [1, 18-25]. For such approaches, designing a framework is critical. Sun et al. (2023) propose a framework consisting of a deductive part and an inductive part. We designed our approach following this framework.
[20] Yican Sun, Xuanyu Peng, Yingfei Xiong*. Synthesizing Efficient Memoization Algorithms. OOPSLA'23: Object-Oriented Programming, Systems, Languages and Applications, October 2023.
输出（请按照JSON格式输出）：
{
    "Citations": [
        {
            "Text": "There are a lot of existing approaches to this problem in recent years [1, 18-25].",
            "Analysis": "作为大量已有工作中的一个进行列举，并没有特别评价。",
            "Positive": false
        },
        {
            "Text": "Sun et al. (2023) propose a framework consisting of a deductive part and an inductive part. We designed our approach following this framework.",
            "Analysis": "参照了被引工作设计了方法框架",
            "Positive": true
        }
    ]
}
"""

short_system = """
用户将提供给你一段某篇论文（称为“引用论文”）中的待分析文本和另一篇论文（称为“被引论文”）的信息，请从文本中提取引用被引论文的句子，并分析这些句子是否正面评价了被引论文。

## 详细解释
* 引用包括
  * 通过编号引用（如“[20, 30]”和“[18-25]”都引用了[20]），
  * 通过作者引用（如“Xiong et al. 2023”引用了Xiong作为一作在2023年撰写的论文），
  * 通过方法名称引用（如“SynMem is ....”引用SynMem）。
  * 注意参考文献本身不应该提取。
* 正面引用包括
  * 称赞被引论文，比如称赞被引论文重要、提出新颖的方法、首次提出了某种思路、效果突出等；
  * 深入参考被引论文内容，比如应用被引论文方法去解决新问题、基于被引论文方法构建新方法等；
  * 在新领域验证被引论文工作，发现论文工作表现突出等。

## 输入输出示例
### 输入：
* 论文信息：Yican Sun, Xuanyu Peng, Yingfei Xiong*. Synthesizing Efficient Memoization Algorithms. OOPSLA'23: Object-Oriented Programming, Systems, Languages and Applications, October 2023.
* 引用编号：[20]
* 方法名称：SynMem
* 待分析文本：Program Synthesis for complex algorithms is an important research problem [1, 18, 25]. There are a lot of existing approaches to this problem in recent years [1, 18-25]. For such approaches, designing a framework is critical. Sun et al. (2023) propose a framework consisting of a deductive part and an inductive part. We designed our approach following this framework.
[20] Yican Sun, Xuanyu Peng, Yingfei Xiong*. Synthesizing Efficient Memoization Algorithms. OOPSLA'23: Object-Oriented Programming, Systems, Languages and Applications, October 2023.
### 输出（请按照JSON格式输出）：
{
    "Citations": [
        {
            "Text": "There are a lot of existing approaches to this problem in recent years [1, 18-25].",
            "Analysis": "作为大量已有工作中的一个进行列举，并没有特别评价。",
            "Positive": false
        },
        {
            "Text": "Sun et al. (2023) propose a framework consisting of a deductive part and an inductive part. We designed our approach following this framework.",
            "Analysis": "参照了被引工作设计了方法框架",
            "Positive": true
        }
    ]
}
### 注意事项
1. 如果待分析文本没有任何引用被引论文的句子，请返回空列表：{"Citations": []}
2. 即使没有正面评价，但引用了被引论文，也应该提取。
3. 请仅输出JSON，不要返回任何其他解释文字。
"""


qwen_system = """
用户将提供给你一段某篇论文（称为“引用论文”）中的待分析文本和另一篇论文（称为“被引论文”）的信息，请从文本中提取引用被引论文的句子，并分析这些句子是否正面评价了被引论文。

## 详细解释
* 引用包括
  * 通过编号引用（如“[20, 30]”和“[18-25]”都引用了[20]），
  * 通过作者引用（如“Sun et al. 2023”引用了Sun在2023年撰写的论文），
  * 通过方法名称引用（如“TreeGen is ....”引用TreeGen）。
* 正面引用包括
  * 称赞被引论文，比如称赞被引论文提出新颖的方法、首次提出了某种思路、效果突出等；
  * 深入参考被引论文内容，比如应用被引论文方法去解决新问题、基于被引论文方法构建新方法等；
  * 在新领域验证被引论文工作，发现论文工作表现突出等。

## 输出格式（请按照如下JSON格式输出）
{"citations": [
    {
        "text": 提取的句子，string类型
        "analysis": 对句子是否是正面评价的分析，string类型
        "positive": 是否是正面评价，bool类型
    }
]}

## 输入输出示例
待分析文本：Program Synthesis for complex algorithms is an important research problem [1, 18, 25]. There are a lot of existing approaches to this problem in recent years [1, 18-25]. For such approaches, designing a framework is critical. Sun et al. (2023) propose a framework consisting of a deductive part and an inductive part. We designed our approach following this framework.
[20] Yican Sun, Xuanyu Peng, Yingfei Xiong*. Synthesizing Efficient Memoization Algorithms. OOPSLA'23: Object-Oriented Programming, Systems, Languages and Applications, October 2023.
输出（请按照JSON格式输出）：
{
    "citations": [
        {
            "text": "There are a lot of existing approaches to this problem in recent years [1, 18-25].",
            "analysis": "作为大量已有工作中的一个进行列举，并没有特别评价。",
            "positive": false
        },
        {
            "text": "Sun et al. (2023) propose a framework consisting of a deductive part and an inductive part. We designed our approach following this framework.",
            "analysis": "参照了被引工作设计了方法框架",
            "positive": true
        }
    ]
}
"""

user_template="""* 论文信息：{paper}
* 引用编号：[{reference_number}]
* 方法名称：{approach_name}
* 待分析文本：
{text}
"""