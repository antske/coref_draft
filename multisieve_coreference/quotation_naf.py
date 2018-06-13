class CquotationNaf:
    '''
    This class encodes source and quotation
    '''

    def __init__(self):
        '''
        Constructor for quotations object
        '''
        self.sip = ''
        self.span = []
        self.source = []
        self.addressee = []
        self.topic = []
        self.beginquote = ''
        self.endquote = ''

    def add_span(self, span):

        self.span = span

    def add_span_id(self, span_id):

        self.span.append(span_id)
