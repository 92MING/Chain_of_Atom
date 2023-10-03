'''You need to set OPENAI_API_KEY in environment variables before running this script.'''

if __name__ == '__main__':
    from data_struct.thinker import Thinker

    thinker = Thinker()
    thinker.think('With only +, -, *, /, how to get 24 from 4, 5, 6, 10?')
