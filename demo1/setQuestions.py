def read_questions(filename):
    answers = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line != '':
                question, answer = line.split('=')
                answers[question.strip()] = answer.strip()
    return answers


def ask_questions(answers):
  correct = []
  wrong = []
  for question, answer in answers.items():
    if input(question + ' - ').strip() == answer:
      print("Corrent!")
      correct.append(question)
    else:
      print("Wrong! The correct answer is %s." % answer)
      wrong.append(question)
  return(correct, wrong)

def stats(correct, wrong, answers):
    print("\n**** STATS ****\n")
    print("You answered", len(correct), "questions correctly and",
          len(wrong), "questions wrong.")

    if wrong:
        print("These would have been the correct answers:")
        for question in wrong:
            print(' ', question, '=', answers[question])

def main():
    filename = input("Name of the question file: ")
    answers = read_questions(filename)
    correct, wrong = ask_questions(answers)
    stats(correct, wrong, answers)

if __name__ == '__main__':
    main()