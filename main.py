import pygame
import pandas as pd
import numpy as np
import re

colors = {'BLACK': (0, 0, 0),
          'GRAY': (127, 127, 127),
          'WHITE': (255, 255, 255),
          'YELLOW': (255, 255, 0),
          'CYAN': (0, 255, 255),
          'MAGENTA': (255, 0, 255),
          'RED': (255, 0, 0),
          'GREEN': (0, 255, 0)
          }

flags = {'mouse_flag': False, 'flag_end_game': False, 'button_pressed': 0}
game_scores = {'right_answers': 0, 'wrong_answers': 0}


class Data_handler():

    def __init__(self, dir):
        try:
            self.data = pd.read_csv(dir)
            self.dir = dir
            self.data['score'].fillna(0, inplace=True)
            self.hebrew_meaning_before_editing = self.data['Hebrew_meaning'].copy()
        except ValueError:
            print("Not a right directory")

    def __del__(self):
        self.data['Hebrew_meaning'] = self.hebrew_meaning_before_editing;
        self.data.to_csv(path_or_buf=self.dir, index=False, encoding='utf-8-sig')

    def get_random_word(self):
        """
        return a dictionary in the same structure:
        dict = {english_word, options_list, correct_option, row_index}
        :return:
        """
        chosen_index = self.get_chosen_english_word_index()
        random_idxes = np.random.randint(len(self.data), size=3)
        random_idxes = np.insert(random_idxes, 0, chosen_index)

        # This make sure that the indexes are not the same
        while len(set(random_idxes)) < 4:
            chosen_index = self.get_chosen_english_word_index()
            random_idxes = np.random.randint(len(self.data), size=3)
            random_idxes = np.insert(random_idxes, 0, chosen_index)

        english_word = self.data.iloc[random_idxes[0]]['English_words']
        hebrew_meanings = np.array(self.data.iloc[random_idxes]['Hebrew_meaning'])

        correct_meaning = hebrew_meanings[0]

        # shuffled:
        hebrew_meanings = np.random.permutation(hebrew_meanings)
        correct_option = np.where(hebrew_meanings == correct_meaning)[0][0] + 1

        return {'english_word': english_word, 'options_list': hebrew_meanings, 'correct_option': correct_option,
                'row_index': random_idxes[0]}

    def get_chosen_english_word_index(self):
        '''
        I used a geometric sidtribution to get more chance for small values
        :return:
        '''
        scores_range = np.array(list(set(self.data['score'])))
        beta = 0.2 + 0.03 * scores_range.max()
        random_score = find_closest(scores_range, np.random.exponential(scale=beta))

        random_idxes_for_score = np.random.randint(len(self.data[self.data['score'] == random_score]))
        # TODO : this line below is usfull for the rest of this function:
        # data.data.loc[data.data['English_words'] == 'fringe'].index[0]
        English_word = self.data[self.data['score'] == random_score]['English_words'].iloc[random_idxes_for_score]
        global_index = self.data.loc[self.data['English_words'] == English_word].index[0]

        return global_index

    def _reset(self):
        '''
        reset al the scores in the exel.
        THIS STEP IS NOT REVERSIBLE!!!!!
        :param val:
        :return:
        '''
        self.data.loc[:, ('score')] = 0
        print('\033[93m' + 'All scores are reset to ZERO' + '\033[0m')


def find_closest(arr, val):
    idx = np.abs(arr - val).argmin()
    return arr[idx]


def print_hebrew_in_pygame(hebrew: str) -> str:
    """
    :param hebrew:
    :return: string in hebrew in the write orientation without vowels
    """
    treshold = 45
    tmp = re.sub(r'[\u0591-\u05BD\u05BF-\u05C2\u05C4-\u05C7]', '', hebrew)
    if len(hebrew) > treshold:
        tmp = tmp[:treshold]
    return tmp[::-1]


def check_if_in_borders(mouse_pos: tuple, object) -> bool:
    x_loc, y_loc = mouse_pos
    if (x_loc <= object.right and x_loc >= object.left) and (y_loc >= object.top and y_loc <= object.bottom):
        return True

    return False  # if not got into the if condition


def draw_button(screen, mouse, pygame_font, text, button_location: tuple, return_val):
    width, height = screen.get_width(), screen.get_height()
    pygame_text = pygame_font.render(text, True, colors['GRAY'])
    button_1 = pygame.draw.rect(screen, colors['WHITE'], [button_location[0], button_location[1], width - 50, 40])
    if check_if_in_borders(mouse, button_1):
        button_1 = pygame.draw.rect(screen, colors['YELLOW'],
                                    [button_location[0], button_location[1], width - 50, 40])
        if flags['mouse_flag']:
            flags['button_pressed'] = return_val

    # superimposing the text onto our button
    screen.blit(pygame_text, (button_1.left, button_1.top))


def exit_button(screen, mouse, pyGame_font):
    exit_text = pyGame_font.render("Exit Game", True, colors['CYAN'])
    width, height = screen.get_width(), screen.get_height()
    button_location = (width // 2 - 200, height - 100)
    button_1 = pygame.draw.rect(screen, colors['WHITE'], [button_location[0], button_location[1], (width * 2) // 3, 60])
    if check_if_in_borders(mouse, button_1):
        button_1 = pygame.draw.rect(screen, colors['GRAY'],
                                    [button_location[0], button_location[1], (height * 2) // 3, 60])
        if flags['mouse_flag']:
            pygame.quit()

    # superimposing the text onto our button
    screen.blit(exit_text, (button_1.centerx - 80, button_1.top))


def main():
    data = Data_handler('words_in_english.csv')
    data.get_chosen_english_word_index()
    # initializing the constructor
    pygame.init()
    pygame.font.init()
    # screen resolution
    res = (720, 720)

    # opens up a window
    screen = pygame.display.set_mode(res)

    width, height = screen.get_width(), screen.get_height()
    arial_35 = pygame.font.SysFont('arial', 35)
    microsoftyaheiui_35 = pygame.font.SysFont('microsoftyaheiui', 35)
    david_35 = pygame.font.SysFont('david', 35)
    david_25 = pygame.font.SysFont('david', 25)
    miriam_35 = pygame.font.SysFont('miriam', 35)
    aharoni_35 = pygame.font.SysFont('aharoni', 35)
    text = david_35.render('עליכם'[::-1], True, colors['CYAN'])
    text = aharoni_35.render(print_hebrew_in_pygame(data.data['Hebrew_meaning'][10]), True, colors['CYAN'])
    unistr1 = "שלום"
    text2 = miriam_35.render(unistr1[::-1], True, colors['RED'])

    # initial text:
    question_dict = data.get_random_word()
    question_text = david_35.render(question_dict['english_word'], True, colors['MAGENTA'])

    prev_text = david_25.render(f"previous correct answer is:", True, colors['GREEN'])
    prev_ans = david_35.render("", True, colors['GREEN'])

    text1 = print_hebrew_in_pygame(question_dict['options_list'][0])
    text2 = print_hebrew_in_pygame(question_dict['options_list'][1])
    text3 = print_hebrew_in_pygame(question_dict['options_list'][2])
    text4 = print_hebrew_in_pygame(question_dict['options_list'][3])

    while True:

        flags['mouse_flag'] = False
        flags['button_pressed'] = -1

        for ev in pygame.event.get():

            if ev.type == pygame.QUIT:
                pygame.quit()

            # checks if a mouse is clicked
            if ev.type == pygame.MOUSEBUTTONDOWN:
                # if the mouse is clicked on the
                # button the game is terminated
                flags['mouse_flag'] = True

        # fills the screen with a color
        screen.fill(colors['BLACK'])

        # stores the (x,y) coordinates into
        # the variable as a tuple
        mouse = pygame.mouse.get_pos()

        # previous correct answer
        previous_ans = pygame.draw.rect(screen, colors['WHITE'], [20, 20, width - 20, 60])
        screen.blit(prev_text, (previous_ans.left + 10, previous_ans.top))
        screen.blit(prev_ans, (previous_ans.left + 10, previous_ans.top + 20))

        # question button
        question = pygame.draw.rect(screen, colors['WHITE'], [20, 100, width - 20, 40])
        screen.blit(question_text, (question.left + 10, question.top + 5))

        # right answers score:
        right_answers = pygame.draw.rect(screen, colors['BLACK'], [100, height - 250, width // 4, 60])
        right_text = arial_35.render(f"The number of correct answers:  {game_scores['right_answers']}",
                                     True, colors['GREEN'])
        screen.blit(right_text, (right_answers.left + 10, right_answers.top))

        # wrong answers score:
        wrong_answers = pygame.draw.rect(screen, colors['BLACK'], [100, height - 200, width // 4, 60])
        wrong_text = arial_35.render(f"The number of wrong answers:  {game_scores['wrong_answers']}",
                                     True, colors['RED'])
        screen.blit(wrong_text, (wrong_answers.left + 10, wrong_answers.top))

        # wrong answers score:
        wrong_answers = pygame.draw.rect(screen, colors['BLACK'], [100, height - 200, width // 4, 60])
        wrong_text = arial_35.render(f"The number of wrong answers:  {game_scores['wrong_answers']}",
                                     True, colors['RED'])
        screen.blit(wrong_text, (wrong_answers.left + 10, wrong_answers.top))

        # exit game
        exit_button(screen, mouse, arial_35)

        draw_button(screen, mouse, aharoni_35, text1, (20, 200), return_val=1)
        draw_button(screen, mouse, aharoni_35, text2, (20, 200 + 50), return_val=2)
        draw_button(screen, mouse, aharoni_35, text3, (20, 200 + 100), return_val=3)
        draw_button(screen, mouse, aharoni_35, text4, (20, 200 + 150), return_val=4)
        # if mouse is hovered on a button it
        # changes to lighter shade

        # get next question and score
        if flags['button_pressed'] > 0:
            prev_ans = david_35.render(question_dict['english_word'] + '=' +
                                       print_hebrew_in_pygame(
                                           question_dict['options_list'][question_dict['correct_option'] - 1]), True,
                                       colors['GREEN'])

            if flags['button_pressed'] == question_dict['correct_option']:
                game_scores['right_answers'] += 1
                # this is to update the score in the relevant answer
                data.data.loc[question_dict['row_index'], ('score')] += 1
            else:
                game_scores['wrong_answers'] += 1
                # this is to update the score in the relevant answer
                if data.data.loc[question_dict['row_index'], ('score')] > 0:
                    data.data.loc[question_dict['row_index'], ('score')] -= 1

            question_dict = data.get_random_word()
            question_text = david_35.render(question_dict['english_word'], True, colors['MAGENTA'])

            text1 = print_hebrew_in_pygame(question_dict['options_list'][0])
            text2 = print_hebrew_in_pygame(question_dict['options_list'][1])
            text3 = print_hebrew_in_pygame(question_dict['options_list'][2])
            text4 = print_hebrew_in_pygame(question_dict['options_list'][3])
        # updates the frames of the game
        pygame.display.update()


if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

# TODO: 1. option to save the results.
#       2. option to differentiate words frequencies
