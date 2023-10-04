'''You need to set OPENAI_API_KEY in environment variables before running this script.'''

if __name__ == '__main__':
    from data_struct.thinker import Thinker
    from atoms.text_atoms import TextToEquations
    thinker = Thinker()
    # thinker.think('With only +, -, *, /, how to get 24 from 4, 5, 6, 10?')
    # thinker.think('7 cups of coffee and 4 pieces of toast cost 655 dollars. 5 cups of coffee and 3 pieces of toast cost 475 dollars. Find the cost of each item.')
    thinker.think('Solve the maths problem "6x+y=18,4x+y=14"')