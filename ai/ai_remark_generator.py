from openai import OpenAI

client = OpenAI(api_key="YOUR_API_KEY")


def generate_remark(issue):

    prompt = f'''
    Generate professional banking concurrent audit remark.

    Issue:
    {issue}
    '''

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content