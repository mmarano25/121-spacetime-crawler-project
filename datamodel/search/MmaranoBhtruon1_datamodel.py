'''
Created on Oct 20, 2016
@author: Rohan Achar
'''
from rtypes.pcc.attributes import dimension, primarykey, predicate
from rtypes.pcc.types.subset import subset
from rtypes.pcc.types.set import pcc_set
from rtypes.pcc.types.projection import projection
from rtypes.pcc.types.impure import impure
from datamodel.search.server_datamodel import Link, ServerCopy

@pcc_set
class MmaranoBhtruon1Link(Link):
    USERAGENTSTRING = "MmaranoBhtruon1"

    @dimension(str)
    def user_agent_string(self):
        return self.USERAGENTSTRING

    @user_agent_string.setter
    def user_agent_string(self, v):
        # TODO (rachar): Make it such that some dimensions do not need setters.
        pass


@subset(MmaranoBhtruon1Link)
class MmaranoBhtruon1UnprocessedLink(object):
    @predicate(MmaranoBhtruon1Link.download_complete, MmaranoBhtruon1Link.error_reason)
    def __predicate__(download_complete, error_reason):
        return not (download_complete or error_reason)


@impure
@subset(MmaranoBhtruon1UnprocessedLink)
class OneMmaranoBhtruon1UnProcessedLink(MmaranoBhtruon1Link):
    __limit__ = 1

    @predicate(MmaranoBhtruon1Link.download_complete, MmaranoBhtruon1Link.error_reason)
    def __predicate__(download_complete, error_reason):
        return not (download_complete or error_reason)

@projection(MmaranoBhtruon1Link, MmaranoBhtruon1Link.url, MmaranoBhtruon1Link.download_complete)
class MmaranoBhtruon1ProjectionLink(object):
    pass
