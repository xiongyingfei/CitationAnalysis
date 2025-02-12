import prompts

class ModelConfig:
    def __init__(self, api_key, base_url, model, pause_seconds, system_prompt, user_prompt_template, response_format):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.pause_seconds = pause_seconds
        self.system_prompt = system_prompt
        self.user_prompt_template = user_prompt_template
        self.response_format = response_format

deepseek_short = ModelConfig(
    api_key="DeepSeekAPIKey",
    base_url="https://api.deepseek.com",
    model="deepseek-chat",
    pause_seconds=0,
    system_prompt=prompts.short_system,
    user_prompt_template=prompts.user_template,
    response_format={'type': 'json_object'}
)

qwen_plus_short = ModelConfig(
    api_key="Ali_API_Key",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",
    pause_seconds=0,
    system_prompt=prompts.short_system,
    user_prompt_template=prompts.user_template,
    response_format={'type': 'text'}
)

model = qwen_plus_short
paper_download_id = "AAAI20"
citation_analysis_id = "AAAI20"




