class Cconstituent_information:
    '''
    This class contains the main constructional information of mentions
    '''

    def __init__(self, head_id, span=None):
        '''
        Constructor for the constituent object
        :param head_id: term id of the head of the constituent
        :param span: list of term ids providing full span of hte constituent
        '''
        self.head_id = head_id
        self.span = span if span is not None else []
        self.multiword = []
        self.modifiers = []
        self.appositives = []
        self.predicatives = []
        self.etype = ''

    def set_span(self, span):

        self.span = span

    def get_span(self):

        return self.span

    def set_multiword(self, mw):

        self.multiword = mw

    def get_multiword(self):

        return self.multiword

    def set_modifiers(self, mods):

        self.modifiers = mods

    def add_modifier(self, mod):

        self.modifiers.append(mod)

    def get_modifiers(self):

        return self.modifiers

    def set_appositives(self, apps):

        self.appositives = apps

    def add_appositive(self, app):

        self.appositives.append(app)

    def get_appositives(self):

        return self.appositives

    def set_predicatives(self, preds):

        self.predicatives = preds

    def add_predicative(self, pred):

        self.predicatives.append(pred)

    def get_predicatives(self):

        return self.predicatives

    def set_etype(self, etype):

        self.etype = etype

    def get_etype(self):

        return self.etype
