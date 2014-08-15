
class SMSToolError(OSError):
    '''root error for SMSToolErrors, shouldn't ever be raised directly'''
    pass

class UnrecognizedDBError(SMSToolError):
    '''Unrecognized sqlite format'''
    pass

class UnfinishedError(SMSToolError):
    '''Not yet implimented'''
    pass
