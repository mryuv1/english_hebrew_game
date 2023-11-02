import pygame
import pandas as pd
import numpy as np
import re
import sys

from bs4 import BeautifulSoup
import requests

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
            game_types_dics = {1: 'add_words', 2: 'know_word_in_english'}

            self.data = pd.read_csv(dir)
            self.dir = dir
            self.data['score'].fillna(0, inplace=True)
            self.hebrew_meaning_before_editing = list(self.data['Hebrew_meaning'].copy())
            self.gameMode = game_types_dics[1]

        except ValueError:
            print("Not a right directory")

    def __del__(self):
        self.data['Hebrew_meaning'] = pd.Series(self.hebrew_meaning_before_editing)
        self.data.to_csv(path_or_buf=self.dir, index=False, encoding='utf-8-sig')

    def add_a_word(self, word, hebrew_meaning):
        check_if_word_excised = self.data['English_words'].isin([word]).any()

        if check_if_word_excised:
            return 0
        else:
            new_row = {'English_words': word, 'Hebrew_meaning': hebrew_meaning, 'score': 0}
            self.hebrew_meaning_before_editing.append(hebrew_meaning)
            self.data.loc[len(self.data)] = new_row

            return 1

    def get_random_english_word(self):
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

        return {'word': english_word, 'options_list': hebrew_meanings, 'correct_option': correct_option,
                'row_index': random_idxes[0]}

    def get_random_hebrew_word(self):
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

        hebrew_word = self.data.iloc[random_idxes[0]]['Hebrew_meaning']
        english_meanings = np.array(self.data.iloc[random_idxes]['English_words'])

        correct_meaning = english_meanings[0]

        # shuffled:
        hebrew_meanings = np.random.permutation(english_meanings)
        correct_option = np.where(hebrew_meanings == correct_meaning)[0][0] + 1

        return {'word': hebrew_word, 'options_list': hebrew_meanings, 'correct_option': correct_option,
                'row_index': random_idxes[0]}

    def get_chosen_english_word_index(self):
        '''
        I used a geometric sidtribution to get more chance for small values
        :return:
        '''
        scores_range = self.data['score'].values
        # beta = 0.2 + 0.03 * scores_range.max()
        # random_score = find_closest(scores_range, np.random.exponential(scale=beta))
        random_score = scores_range.min()
        # random_idxes_for_score = np.random.randint(len(self.data[self.data['score'] == random_score]))
        # TODO : this line below is usfull for the rest of this function:
        # data.data.loc[data.data['English_words'] == 'fringe'].index[0]
        global_index = self.data[self.data['score'] == random_score].sample(n=1).index[0]

        # global_index = self.data.loc[self.data['English_words'] == English_word].index[0]

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


def search_word_in_morfix(search_word):
    try:
        url = 'https://www.morfix.co.il/' + search_word
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html')
        translation = soup.find('div', class_='Translation_divMiddle_enTohe')
        pattern = r'[\u0590-\u05FF\s;]+'
        hebrew_text = re.findall(pattern, str(translation))
        hebrew_text = ''.join(hebrew_text).strip()
    except:
        return (0, "No result")

    if hebrew_text:
        return (1, hebrew_text)
    else:
        try:
            suggestions = soup.find('ul', class_='list-inline Suggestions_ulbottom_enTohe')
            # Define the start and end substrings
            start_substring = "Translation', '"
            end_substring = "');"

            # Create a regex pattern to match everything between the start and end substrings
            pattern = re.escape(start_substring) + r'(.*?)' + re.escape(end_substring)

            # Check if a match was found
            options_string = ""
            suggestions = list(suggestions)
            for idx in range(len(suggestions)):
                suggestion = suggestions[idx]
                match = re.search(pattern, str(suggestion))
                if match:
                    # Extract the substring between the start and end substrings
                    extracted_substring = match.group(1)
                    options_string = options_string + match.group(1) + ", "

            options_string = options_string[:-2]
            return (0, options_string)
        except:
            return (0, "No result")


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


screen_properties = {'SCREEN_WIDTH': 800, 'SCREEN_HEIGHT': 600, 'FPS': 60}

# Initialize the screen
screen = pygame.display.set_mode((screen_properties['SCREEN_WIDTH'], screen_properties['SCREEN_HEIGHT']))
pygame.display.set_caption("Screen Switching with Buttons")


# Define a Button class
class Button:
    """
    The input is a button dict in the form of:
    {'x': int,
     'y': int,
     'width': int,
     'height': int
     'text': string,
     'callback': function to go to,
     'back_color': (optional),
     'text_color': (optional),
     'font': (optional),
     'allow_callback'" (optional),
     'return_value': (optional in case of disable callback),
     'mouse_pointer_color':(optional)}
    """

    def __init__(self, **kwargs):  # x, y, width, height, text, callback, back_color='GRAY', text_color='BLACK'):

        self.rect_object = None
        self.rect = pygame.Rect(kwargs.get('x'), kwargs.get('y'), kwargs.get('width'), kwargs.get('height'))
        self.text = kwargs.get('text')
        self.callback = kwargs.get('callback', None)
        self.font = kwargs.get('font', pygame.font.Font(None, 36))
        self.back_color = kwargs.get('back_color', 'GRAY')
        self.text_color = kwargs.get('text_color', 'BLACK')
        self.frame_color = kwargs.get('frame_color', self.back_color)
        self.mouse_pointer_color = kwargs.get('mouse_pointer_color', None)
        self.allow_callback = kwargs.get('allow_callback', 1)
        self.return_value = kwargs.get('return_value', 0)
        self.current_background_color = self.back_color

    def draw(self):
        self.rect_object = pygame.draw.rect(screen, self.current_background_color, self.rect)
        pygame.draw.rect(screen, self.frame_color, self.rect, 2)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def mouse_on_button(self, mouse_position):
        if check_if_in_borders(mouse_position, self.rect_object) and self.mouse_pointer_color:
            self.current_background_color = self.mouse_pointer_color
        else:
            self.current_background_color = self.back_color

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.allow_callback:
                    flags['button_pressed'] = self.return_value
                    self.callback()
                else:
                    flags['button_pressed'] = self.return_value


# Create the menu and game screen functions
def menu_screen():
    buttons = [Button(**{'x': 200,
                         'y': 150,
                         'width': 400,
                         'height': 50,
                         'text': "Start Game (English words)",
                         'mouse_pointer_color': 'WHITE',
                         'callback': game_screen,
                         'return_value': 5}),
               Button(**{'x': 200,
                         'y': 250,
                         'width': 400,
                         'height': 50,
                         'text': "Start Game (Hebrew words)",
                         'mouse_pointer_color': 'WHITE',
                         'callback': game_screen,
                         'return_value': 6}),
               Button(**{'x': 200,
                         'y': 350,
                         'width': 400,
                         'height': 50,
                         'text': "Search & Insert New Words",
                         'mouse_pointer_color': 'WHITE',
                         'callback': enter_word}),
               Button(**{'x': 200,
                         'y': 450,
                         'width': 400,
                         'height': 50,
                         'text': "Quit",
                         'mouse_pointer_color': 'WHITE',
                         'callback': quit_game})
               ]
    # buttons = [Button({200, 200, 400, 50, "Start Game", game_screen),
    #            Button(200, 300, 400, 50, "Search & Insert New Words", enter_word),
    #            Button(200, 400, 400, 50, "Quit", quit_game)]
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            for button in buttons:
                button.handle_event(event)

        screen.fill(colors['BLACK'])
        for button in buttons:
            mouse = pygame.mouse.get_pos()
            button.draw()
            button.mouse_on_button(mouse)
        pygame.display.flip()


# ...

# Create the game screen function
def game_screen():
    data.get_chosen_english_word_index()

    arial_35 = pygame.font.SysFont('arial', 35)
    david_35 = pygame.font.SysFont('david', 35)
    david_25 = pygame.font.SysFont('david', 25)
    aharoni_35 = pygame.font.SysFont('aharoni', 35)

    if flags['button_pressed'] == 5:
        use_english_not_hebrew = 1
    else:
        use_english_not_hebrew = 0

    # reset button value
    flags['button_pressed'] = 0
    # initial text:
    if use_english_not_hebrew:
        question_dict = data.get_random_english_word()
    else:
        question_dict = data.get_random_hebrew_word()

    buttons = [Button(**{'x': 150,  # 0
                         'y': 530,
                         'width': 200,
                         'height': 50,
                         'text': "Back to Menu",
                         'mouse_pointer_color': "WHITE",
                         'callback': menu_screen}),
               Button(**{'x': 450,  # 1
                         'y': 530,
                         'width': 200,
                         'height': 50,
                         'text': "Quit",
                         'mouse_pointer_color': "WHITE",
                         'callback': quit_game}),
               Button(**{'x': 50,  # 2
                         'y': 30,
                         'width': 400,
                         'height': 30,
                         'text': "previous correct answer is: ",
                         'back_color': 'BLACK',
                         'text_color': 'GREEN',
                         'font': david_25,
                         'allow_callback': False}),
               Button(**{'x': 10,  # 3
                         'y': 60,
                         'width': 780,
                         'height': 30,
                         'text': f"",
                         'back_color': 'BLACK',
                         'text_color': 'GREEN',
                         'font': david_25,
                         'allow_callback': False}),
               Button(**{'x': 100,  # 4
                         'y': 420,
                         'width': 400,
                         'height': 30,
                         'text': f"Number of correct answers: {game_scores['right_answers']}",
                         'back_color': 'BLACK',
                         'text_color': 'GREEN',
                         'font': arial_35,
                         'allow_callback': False}),
               Button(**{'x': 100,  # 5
                         'y': 470,
                         'width': 400,
                         'height': 30,
                         'text': f"Number of wrong answers: {game_scores['wrong_answers']}",
                         'back_color': 'BLACK',
                         'text_color': 'RED',
                         'font': arial_35,
                         'allow_callback': False}),

               # question_text = david_35.render(question_dict['english_word'], True, colors['MAGENTA'])
               # question button:
               Button(**{'x': 50,  # 6
                         'y': 140,
                         'width': 700,
                         'height': 50,
                         'text': question_dict['word'] if use_english_not_hebrew else print_hebrew_in_pygame(
                             question_dict['word']),
                         'font': david_35,
                         'allow_callback': False}),

               # the answers button:
               Button(**{'x': 10,  # 7
                         'y': 200,
                         'width': 780,
                         'height': 50,
                         'text': print_hebrew_in_pygame(question_dict['options_list'][0]) if use_english_not_hebrew else
                         question_dict['options_list'][0],
                         'font': aharoni_35,
                         'mouse_pointer_color': "YELLOW",
                         'allow_callback': False,
                         'return_value': 1}),
               Button(**{'x': 10,  # 8
                         'y': 200 + 50,
                         'width': 780,
                         'height': 50,
                         'text': print_hebrew_in_pygame(question_dict['options_list'][1]) if use_english_not_hebrew else
                         question_dict['options_list'][1],
                         'font': aharoni_35,
                         'mouse_pointer_color': "YELLOW",
                         'allow_callback': False,
                         'return_value': 2}),
               Button(**{'x': 10,  # 9
                         'y': 200 + 100,
                         'width': 780,
                         'height': 50,
                         'text': print_hebrew_in_pygame(question_dict['options_list'][2]) if use_english_not_hebrew else
                         question_dict['options_list'][2],
                         'font': aharoni_35,
                         'mouse_pointer_color': "YELLOW",
                         'allow_callback': False,
                         'return_value': 3}),
               Button(**{'x': 10,  # 10
                         'y': 200 + 150,
                         'width': 780,
                         'height': 50,
                         'text': print_hebrew_in_pygame(question_dict['options_list'][3]) if use_english_not_hebrew else
                         question_dict['options_list'][3],
                         'font': aharoni_35,
                         'mouse_pointer_color': "YELLOW",
                         'allow_callback': False,
                         'return_value': 4})
               ]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            for button in buttons:
                button.handle_event(event)

            screen.fill(colors['BLACK'])
        for button in buttons:
            mouse = pygame.mouse.get_pos()
            button.draw()
            button.mouse_on_button(mouse)
        pygame.display.flip()

        if flags['button_pressed'] > 0:
            # prev answer text:
            buttons[3].text = (question_dict['word'] + '=' + print_hebrew_in_pygame(
                question_dict['options_list'][question_dict['correct_option'] - 1])) if use_english_not_hebrew else (
                    question_dict['options_list'][
                        question_dict['correct_option'] - 1] + '=' + print_hebrew_in_pygame(question_dict['word']))

            if flags['button_pressed'] == question_dict['correct_option']:
                game_scores['right_answers'] += 1
                # this is to update the score in the relevant answer
                data.data.loc[question_dict['row_index'], ('score')] += 1
            else:
                game_scores['wrong_answers'] += 1
                # this is to update the score in the relevant answer
                if data.data.loc[question_dict['row_index'], ('score')] > 0:
                    data.data.loc[question_dict['row_index'], ('score')] -= 1

            # get words for the next round
            if use_english_not_hebrew:
                question_dict = data.get_random_english_word()
            else:
                question_dict = data.get_random_hebrew_word()

            buttons[4].text = f"Number of correct answers: {game_scores['right_answers']}"
            buttons[5].text = f"Number of wrong answers: {game_scores['wrong_answers']}"
            buttons[6].text = question_dict['word'] if use_english_not_hebrew else print_hebrew_in_pygame(
                question_dict['word'])
            buttons[7].text = print_hebrew_in_pygame(question_dict['options_list'][0]) if use_english_not_hebrew else \
                question_dict['options_list'][0]
            buttons[8].text = print_hebrew_in_pygame(question_dict['options_list'][1]) if use_english_not_hebrew else \
                question_dict['options_list'][1]
            buttons[9].text = print_hebrew_in_pygame(question_dict['options_list'][2]) if use_english_not_hebrew else \
                question_dict['options_list'][2]
            buttons[10].text = print_hebrew_in_pygame(question_dict['options_list'][3]) if use_english_not_hebrew else \
                question_dict['options_list'][3]

            flags['button_pressed'] = 0


# ...

def enter_word():
    david_35 = pygame.font.SysFont('david', 35)
    flags['button_pressed'] = 0
    buttons = [Button(**{'x': 150,  # 0
                         'y': 500,
                         'width': 200,
                         'height': 50,
                         'text': "Back to Menu",
                         'mouse_pointer_color': "WHITE",
                         'callback': menu_screen}),
               Button(**{'x': 450,  # 1
                         'y': 500,
                         'width': 200,
                         'height': 50,
                         'text': "Quit",
                         'mouse_pointer_color': "WHITE",
                         'callback': quit_game}),
               Button(**{'x': 50,  # 2
                         'y': 30,
                         'width': 400,
                         'height': 30,
                         'text': "Enter word for search: ",
                         'back_color': 'BLACK',
                         'text_color': 'WHITE',
                         'allow_callback': False}),
               Button(**{'x': 10,  # 3
                         'y': 80,
                         'width': 780,
                         'height': 30,
                         'text': "",
                         'back_color': 'GRAY',
                         'text_color': 'BLACK',
                         'allow_callback': False}),
               Button(**{'x': 10,  # 4
                         'y': 120,
                         'width': 780,
                         'height': 100,
                         'text': "",
                         'back_color': 'GRAY',
                         'text_color': 'BLACK',
                         'font': david_35,
                         'allow_callback': False}),
               Button(**{'x': 180,  # 5
                         'y': 250,
                         'width': 450,
                         'height': 50,
                         'text': "search for a new word (no save)",
                         'back_color': 'GRAY',
                         'text_color': 'RED',
                         'mouse_pointer_color': "YELLOW",
                         'font': david_35,
                         'allow_callback': True,
                         'callback': enter_word}),
               Button(**{'x': 180,  # 6
                         'y': 320,
                         'width': 450,
                         'height': 50,
                         'text': "save word",
                         'back_color': 'GRAY',
                         'text_color': 'GREEN',
                         'font': david_35,
                         'mouse_pointer_color': "YELLOW",
                         'allow_callback': False,
                         'return_value': 1
                         }),
               Button(**{'x': 180,  # 7
                         'y': 390,
                         'width': 450,
                         'height': 50,
                         'text': "",
                         'back_color': 'BLACK',
                         'text_color': 'GREEN',
                         'font': david_35,
                         'allow_callback': False,
                         'return_value': 1
                         })
               ]

    input_text = ""
    search_text = ""
    input_active = True
    search_flag = 1

    # buttons = [Button(150, 500, 200, 50, "Back to Menu", menu_screen),
    #            Button(450, 500, 200, 50, "Quit", quit_game)]
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if input_active:
                    if event.key == pygame.K_RETURN:
                        input_active = False
                        parse_text(input_text)
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode

            for button in buttons:
                button.handle_event(event)

        buttons[3].text = input_text

        if not input_active:
            if search_flag:
                morfix_scraping = search_word_in_morfix(input_text)
                search_flag = 0

            if morfix_scraping[0]:
                buttons[4].text = print_hebrew_in_pygame(morfix_scraping[1])
            else:
                buttons[4].text = f"There is no result, maybe try:  {morfix_scraping[1]}"

        if (flags['button_pressed'] > 0) and not input_active:
            add_result = data.add_a_word(word=input_text, hebrew_meaning=morfix_scraping[1])
            if add_result:
                buttons[7].text = "word was added"
                buttons[7].text_color = "GREEN"
            else:
                buttons[7].text = "word was already in the system"
                buttons[7].text_color = "RED"

            flags['button_pressed'] = 0

        screen.fill(colors['BLACK'])
        for button in buttons:
            mouse = pygame.mouse.get_pos()
            button.draw()
            button.mouse_on_button(mouse)
        pygame.display.flip()


def quit_game():
    data.__del__()
    pygame.quit()
    sys.exit()


def parse_text(input_text):
    # Example: Split the input text into words
    words = input_text.split()
    print("Parsed Words:", words)


if __name__ == '__main__':
    global data
    # Initialize Pygame
    pygame.init()
    data = Data_handler(dir='words_in_english.csv')
    menu_screen()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

# TODO: 1. option to save the results.
#       2. option to differentiate words frequencies
