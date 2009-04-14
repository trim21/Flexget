import urllib2
from feed import Entry
import re
import logging

log = logging.getLogger('text')

class InputText:

    """
    Parse any text for entries using regular expression.

    url: <url>
    entry:
      <field>: <regexp to match value>
    format:
      <field>: <python string formatting>

    Note: each entry must have atleast two fields, title and url

    Example:

    text:
      url: http://www.nbc.com/Heroes/js/novels.js
      entry:
        title: novelTitle = "(.*)"
        url: novelPrint = "(.*)"
      format:
        url: http://www.nbc.com%(url)s

    """

    def register(self, manager, parser):
        manager.register('text')

    def validator(self):
        import validator
        text = validator.factory('dict')
        text.accept('url', key='url', required=True)
        entry = text.accept('dict', key='entry', required=True)
        entry.accept('url', key='url', required=True)
        entry.accept('text', key='title', required=True)
        entry.accept_any_key('text')
        format = text.accept('dict', key='format')
        format.accept_any_key('text')
        return format

    def format_entry(self, entry, d):
        for k, v in d.iteritems():
            entry[k] = v % entry

    def feed_input(self, feed):
        url = feed.config['text']['url']
        content = urllib2.urlopen(url)

        entry_config = feed.config['text'].get('entry')
        format_config = feed.config['text'].get('format', {})

        # keep track what fields have been found
        used = {}
        entry = Entry()

        # now parse text
        for line in content:
            for field, regexp in entry_config.iteritems():
                #log.debug('search field: %s regexp: %s' % (field, regexp))
                match = re.search(regexp, line)
                if match:
                    # check if used field detected, in such case start with new entry
                    if used.has_key(field):
                        if entry.isvalid():
                            log.info('Found field %s again before entry was completed. Adding current incomplete, but valid entry and moving to next.' % field)
                            self.format_entry(entry, format_config)
                            feed.entries.append(entry)
                        else:
                            log.info('Invalid data, entry field %s is already found. Ignoring entry.' % field)
                        # start new entry
                        entry = Entry()
                        used = {}
                        
                    # add field to entry
                    entry[field] = match.group(1)
                    used[field] = True
                    log.debug('found field: %s value: %s' % (field, entry[field]))

                # if all fields have been found
                if len(used) == len(entry_config):
                    # check that entry has atleast title and url
                    if not entry.isvalid():
                        log.info('Invalid data, constructed entry is missing mandatory fields (title or url)')
                    else:
                        self.format_entry(entry, format_config)
                        feed.entries.append(entry)
                        log.debug('Added entry %s' % entry)
                        # start new entry
                        entry = Entry()
                        used = {}