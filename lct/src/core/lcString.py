import re


class String(object):

    @classmethod
    def validate_starts_with_digit(cls, string, *args, **kwargs):
        '''
        node names in Maya cannot start with a digit
        removes starting digits and underscores
        '''
        if string:
            if string[0].isdigit():
                string = string[1:]
                string = cls.rem_leading(string)
        return string

    @classmethod
    def split_at_uppercase(cls, string, *args, **kwargs):
        '''
        theBrownCat > [the, Brown, Cat]
        '''
        return re.sub(r"([A-Z])", r" \1", string).split()

    @classmethod
    def split_at_digits(cls, string, *args, **kwargs):
        '''
        abc123de45 > [abc, 123, de, 45]
        '''
        l = re.split('(\d+)', string)
        l = filter(None, l)
        return l

    @classmethod
    def rem_trailing(cls, string, rem='_', *args, **kwargs):
        '''
        match rem to trailing character and remove
        '''
        return re.sub(re.escape(rem) + '$', "", string)

    @classmethod
    def rem_leading(cls, string, rem='_', *args, **kwargs):
        '''
        match rem to leading characters and remove
        '''
        return re.sub('^' + re.escape(rem), "", string)

    @classmethod
    def add_prefix(cls, string, prefix, *args, **kwargs):
        ''' '''
        prefix = cls.rem_trailing(prefix)
        string = cls.rem_leading(string)
        if prefix:
            string = '{}_{}'.format(prefix, string)
        return string

    @classmethod
    def add_suffix(cls, string, suffix, *args, **kwargs):
        ''' '''
        string = cls.rem_trailing(string)
        suffix = cls.rem_leading(suffix)
        if suffix:
            string = '{}_{}'.format(string, suffix)
        return string

    @classmethod
    def search_and_replace(cls, string, searchTerm, replaceTerm, underscore=False, *args, **kwargs):
        ''' '''
        string = string.replace(searchTerm, replaceTerm)
        if underscore:
            string = cls.rem_leading(string)
            string = cls.rem_trailing(string)
        return string

    @classmethod
    def rename_and_number(cls, newName, num, pad, *args, **kwargs):
        ''' '''
        num = str(num).zfill(pad)  # format(num, '0{}'.format(pad))

        return '{}{}'.format(newName, num)
