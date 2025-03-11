from openai import OpenAI

def run_script():
    """OpenAI API 호출"""


    client = OpenAI()


    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "hello"}],  # 올바른 메시지 형식 적용
        response_format={"type": "text"},  # ✅ 객체 형태로 수정
        temperature=1,
        max_tokens=2048,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )


    return response.choices[0].message.content  # 응답 내용 반환

if __name__ == '__main__':
    print(run_script())  # Print the generated response
