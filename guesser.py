from random import choice
import yaml
from rich.console import Console
import math
import numpy as np
from collections import Counter
from collections import defaultdict

class Guesser:
    '''
        INSTRUCTIONS: This function should return your next guess. 
        Currently it picks a random word from wordlist and returns that.
        You will need to parse the output from Wordle:
        - If your guess contains that character in a different position, Wordle will return a '-' in that position.
        - If your guess does not contain thta character at all, Wordle will return a '+' in that position.
        - If you guesses the character placement correctly, Wordle will return the character. 

        You CANNOT just get the word from the Wordle class, obviously :)
    '''
    def __init__(self, manual):
        self.word_list = yaml.load(open('wordlist.yaml'), Loader=yaml.FullLoader)
        self._manual = manual
        self.console = Console()
        self._tried = []
        
    def restart_game(self):
        self._tried = []
        
        self.alphabet = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
        matrix = np.zeros((len(self.word_list), len(self.alphabet)+1))
        matrix[:, -1] = np.arange(len(self.word_list)) #to keep the index
        counter = 0
        for word in self.word_list:
            letters = Counter(word)
            for k, v in letters.items():
                matrix[counter][self.alphabet.index(k)] = v
            counter += 1
        self.matrix = matrix
        
        #tracking indices of the letters
        char_order_matrix = np.array([list(word) for word in self.word_list])
        idx = np.arange(len(self.word_list)) #to keep track of indices
        char_order_matrix = np.column_stack((char_order_matrix, idx))
        self.char_order_matrix = char_order_matrix

    def entropy(self, matrix):
        entr_m = matrix[:, :-1].copy()
        total = entr_m.sum()
        if total == 0:
            return choice(self.word_list)
        prob = entr_m.sum(axis=0) / total
        entropy = [elem * math.log2(elem) if elem > 0 else 0 for elem in prob]
        somma_entropy = -(entropy * entr_m).sum(axis=1)
        #print(f"entropy words: {len(matrix)} sum: {somma_entropy}")
                        
        #i don't want it to select doubles (eg two Ls or two Es) that often because it gives less info
        no_doubles = np.array([self.less_doubles(self.word_list[int(idx)]) for idx in matrix[:, -1]])
        final_entropy = somma_entropy - no_doubles        
        
        #now I want to get the original index for the word
        idx_max_entr = int(matrix[np.argmax(final_entropy), -1])

        return self.word_list[idx_max_entr]
        
    def less_doubles(self, word):
        return sum(word.count(letter) - 1 for letter in set(word))
            
    def get_guess(self, result):
        '''
        This function must return your guess as a string. 
        '''
        if self._manual=='manual':
            return self.console.input('Your guess:\n')
        if len(self._tried) != 0:
            #guess = "roate"
        #else:
            letters_in_word = defaultdict(int)
            letters_not_in_word = defaultdict(int)
            char_order = defaultdict(str)
            not_right_positions = defaultdict(int)
            
            #checking the pattern based on previous guess
            for i in range(len(result)):
                if result[i] != "+" and result[i] != "-":
                    letters_in_word[result[i]] += 1
                    char_order[i] = result[i]
                if result[i] == "-":
                    letters_in_word[self._tried[-1][i]] += 1
                    not_right_positions[self._tried[-1][i]] = i
                if result[i] == "+":
                    if self._tried[-1][i] in letters_in_word.keys(): #if hanna has one valid "a", I need the count for "a"s to be 1
                        letters_not_in_word[self._tried[-1][i]] = 1
                    else: #the letter is not even once in the word
                        letters_not_in_word[self._tried[-1][i]] = 0
            
            for letter in letters_not_in_word.keys():
                if letter in letters_in_word:
                    letters_not_in_word[letter] = letters_in_word[letter]

            #filtering the matrix: I keep only the words that match what I want
            wanted_cols = [(self.alphabet.index(letter.lower()), conto) for letter, conto in letters_in_word.items()] #I check the columns of the letters of my word
            eliminate_cols = [(self.alphabet.index(letter.lower()), conto) for letter, conto in letters_not_in_word.items()] #letters I don't want: I can erase all the words with these letters
            #also eliminate all the words which have letters that aren't needed
            
            #I also filter the other char_order_matrix to get only the words with right order
            for k, v in char_order.items():
                self.char_order_matrix = self.char_order_matrix[self.char_order_matrix[:, k] == v]
                
            for k, v in not_right_positions.items():
                self.char_order_matrix = self.char_order_matrix[self.char_order_matrix[:, v] != k]
                
            idx_ok = self.char_order_matrix[:, -1].astype(int) #indices to keep
            self.matrix = self.matrix[np.isin(self.matrix[:, -1].astype(int), idx_ok)]
            
            wanted_mask = (np.all([self.matrix[:, cols] >= conto for cols, conto in wanted_cols], axis=0))
            eliminate_mask = (np.all([self.matrix[:, cols] == conto for cols, conto in eliminate_cols], axis=0))
            self.matrix = self.matrix[wanted_mask & eliminate_mask] #I keep the words where the letter is there
            
            #remove last guess
            if self._tried[-1] in self.word_list:
                just_tried = self.word_list.index(self._tried[-1])
                self.matrix = self.matrix[self.matrix[:, -1] != just_tried]
        
        guess = self.entropy(self.matrix)
        
        self._tried.append(guess)
        self.console.print(guess)
        return guess
        

        