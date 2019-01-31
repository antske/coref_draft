class Cquotation:
    '''
    This class encodes source and quotation
    '''

    def __init__(self, sip):
        '''
        Constructor for quotations object
        '''
        self.sip = sip
        self.span = None
        self.string = None
        self.beginOffset = None
        self.endOffset = None
        self.source = None
        self.addressee = None
        self.topic = None

    def set_span(self, span):

        self.span = span

    def get_span(self):

        return self.span

    def set_string(self, mystring):

        self.string = mystring

    def get_string(self):

        return self.string

    def set_begin_offset(self, boffset):

        self.beginOffset = boffset

    def get_begin_offset(self):

        return self.beginOffset

    def set_end_offset(self, eoffset):
        self.endOffset = eoffset

    def get_end_offset(self):
        return self.endOffset

    def set_source(self, source):
        self.source = source

    def get_source(self):
        return self.source

    def set_addressee(self, addressee):
        self.addressee = addressee

    def get_addressee(self):
        return self.addressee

    def set_topic(self, topic):
        self.topic = topic

    def get_topic(self):
        return self.topic
