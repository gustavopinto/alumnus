from .dispatcher import dispatcher, notifies
from .channels.email import EmailChannel
from . import events

dispatcher.register(EmailChannel())
