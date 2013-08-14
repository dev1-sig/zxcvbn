#!/usr/bin/python

import os
import time
import codecs
import urllib
import simplejson
import urllib2
import re
import unicodedata, sys

from pprint import pprint

SLEEP_TIME = 20 # seconds

def get_ranked_english():
    '''
    wikitionary has a list of ~40k English words, ranked by frequency of occurance in TV and movie transcripts.
    more details at:
    http://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/TV/2006/explanation

    the list is separated into pages of 1000 or 2000 terms each.
    * the first 10k words are separated into pages of 1000 terms each.
    * the remainder is separated into pages of 2000 terms each:
    '''
    URL_TMPL = 'http://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/TV/2006/%s'
    urls = []
    for i in xrange(10):
        freq_range = "%d-%d" % (i * 1000 + 1, (i+1) * 1000)
        urls.append(URL_TMPL % freq_range)

    for i in xrange(0,15):
        freq_range = "%d-%d" % (10000 + 2 * i * 1000 + 1, 10000 + (2 * i + 2) * 1000)
        urls.append(URL_TMPL % freq_range)

    urls.append(URL_TMPL % '40001-41284')

    ranked_terms = [] # ordered by rank, in decreasing frequency.
    for url in urls:
        html, is_cached = english_wiki_download(url)

        new_terms = parse_wiki_terms(html)
        ranked_terms.extend(new_terms)

    return ranked_terms

def english_wiki_download(url):
    freq_range = url[url.rindex('/')+1:]

    tmp_path = '../data/tv_and_movie_freqlist%s.html' % freq_range
    return wiki_download(url, tmp_path)

def wiki_download(url, tmp_path):
    '''
    scrape friendly: sleep 20 seconds between each request, cache each result.
    '''
    if os.path.exists(tmp_path):
        print 'cached.......', url
        with codecs.open(tmp_path, 'r', 'utf8') as f:
            return f.read(), True
    with codecs.open(tmp_path, 'w', 'utf8') as f:
        print 'downloading...', url
        req = urllib2.Request(url, headers={
                'User-Agent': 'zxcvbn'
                })
        response = urllib2.urlopen(req)
        result = response.read().decode('utf8')
        f.write(result)
        time.sleep(SLEEP_TIME)
        return result, False

def parse_wiki_terms(doc):
    '''
    who needs an html parser. fragile hax, but checks the result at the end
    '''
    results = []
    last3 = ['', '', '']
    header = True
    for line in doc.split('\n'):
        last3.pop(0)
        last3.append(line.strip())
        if all(s.startswith('<td>') and not s == '<td></td>' for s in last3):
            if header:
                header = False
                continue
            last3 = [s.replace('<td>', '').replace('</td>', '').strip() for s in last3]
            rank, term, count = last3
            rank = int(rank.split()[0])
            term = term.replace('</a>', '')
            term = term[term.index('>')+1:].lower()
            results.append(term)
    assert len(results) in [1000, 2000, 1284] # early docs have 1k entries, later have 2k, last doc has 1284
    return results

def get_ranked_census_names():
    '''
    takes name lists from the the 2000 us census, prepares as a json array in order of frequency (most common names first).

    more info:
    http://www.census.gov/genealogy/www/data/2000surnames/index.html

    files in data are downloaded copies of:
    http://www.census.gov/genealogy/names/dist.all.last
    http://www.census.gov/genealogy/names/dist.male.first
    http://www.census.gov/genealogy/names/dist.female.first
    '''
    FILE_TMPL = '../data/us_census_2000_%s.txt'
    SURNAME_CUTOFF_PERCENTILE = 85 # ie7 can't handle huge lists. cut surname list off at a certain percentile.
    lists = []
    for list_name in ['surnames', 'male_first', 'female_first']:
        path = FILE_TMPL % list_name
        lst = []
        for line in codecs.open(path, 'r', 'utf8'):
            if line.strip():
                if list_name == 'surnames' and float(line.split()[2]) > SURNAME_CUTOFF_PERCENTILE:
                    break
                name = line.split()[0].lower()
                lst.append(name)
        lists.append(lst)
    return lists

def get_ranked_common_passwords():
    lst = []
    for line in codecs.open('../data/common_passwords.txt', 'r', 'utf8'):
        if line.strip():
            lst.append(line.strip())
    return lst


'''
--------------------------------------------------
Chinese dictionary build - START
--------------------------------------------------
'''

# ------------ Chinese surnames
def get_chinese_surnames():
    urls = []
    urls.append("http://www.mandarinhouse.com/100-common-chinese-family-names")

    ranked_terms = []
    for url in urls:
        html, is_cached = wiki_download(url, '../data/Chinese_surnames.html')

        new_terms = parse_chinese_wiki(html, r'^<p>\d.*?([\w\-]+)</p>.*$', r'^<p>\d.*')
        ranked_terms.extend(new_terms)

    return ranked_terms

# ------------ Chinese names
def get_chinese_names():
	urls = []
	urls.append("http://www.top-100-baby-names-search.com/female-chinese-names.html")
	urls.append("http://www.top-100-baby-names-search.com/chinese-girl-names.html")
	urls.append("http://www.top-100-baby-names-search.com/chinese-male-names.html")
	urls.append("http://www.top-100-baby-names-search.com/chinese-boys-names.html")

	ranked_terms = []
	for url in urls:
		# we want all Chinese files to start with word Chinese
		tmp_path = '../data/Chinese_names_%s' %  url[url.rindex('/')+1:].replace("chinese-", "")

		html, is_cached = wiki_download(url, tmp_path)

		new_terms = parse_chinese_wiki(html, r'.*<td width="25%" class="tablecellstyle[89]+">([\w\s\-]+)</td>.*$', r'.*<p>\d+.*')
		ranked_terms.extend(new_terms)

	return ranked_terms


# ------------ Chinese freq words

def get_chinese_freq_words():
	URL_TMPL = 'http://en.wiktionary.org/wiki/Appendix:Mandarin_Frequency_lists/%s'
	urls = []
	for i in xrange(10):
		freq_range = "%d-%d" % (i * 1000 + 1, (i+1) * 1000)
		urls.append(URL_TMPL % freq_range)

	ranked_terms = [] # ordered by rank, in decreasing frequency.
	for url in urls:
		tmp_path = '../data/Chinese_Frequency_lists_%s.html' % url[url.rindex('/')+1:]

		html, is_cached = wiki_download(url, tmp_path)

		new_terms = parse_chinese_wiki(html, r'.*>(.*)</a>\).*', r'^.*<li>.*')
		ranked_terms.extend(new_terms)

	return ranked_terms

## -------------------------------------------------------------
# ------------ Chinese parsing and character mapping functions

def parse_chinese_wiki(doc, regex_term, regex_start_line):
    results = []
    for line in doc.split('\n'):
		line = line.lower().translate(unaccented_map())
		matchObj = re.match(regex_term, line, re.S)
		if matchObj:
			terms = matchObj.group(1).strip()
			terms = terms.replace("-", " ")
			for term in terms.split():
				if term not in results:
					results.append(term)
		else:
			if re.match(regex_start_line, line, re.S):
				print "\nCannot process line: \n"
				print line

    return results

# Translation dictionary.  Translation entries are added to this
# dictionary as needed.

class unaccented_map(dict):

    ##
    # Maps a unicode character code (the key) to a replacement code
    # (either a character code or a unicode string).

    def mapchar(self, key):
        ch = self.get(key)
        if ch is not None:
            return ch
        de = unicodedata.decomposition(unichr(key))
        if de:
            try:
                ch = int(de.split(None, 1)[0], 16)
            except (IndexError, ValueError):
                ch = key
        else:
            ch = CHAR_REPLACEMENT.get(key, key)
        self[key] = ch
        return ch

    if sys.version >= "2.5":
        # use __missing__ where available
        __missing__ = mapchar
    else:
        # otherwise, use standard __getitem__ hook (this is slower,
        # since it's called for each character)
        __getitem__ = mapchar

CHAR_REPLACEMENT = {
    # latin-1 characters that don't have a unicode decomposition
    0xc6: u"AE", # LATIN CAPITAL LETTER AE
    0xd0: u"D",  # LATIN CAPITAL LETTER ETH
    0xd8: u"OE", # LATIN CAPITAL LETTER O WITH STROKE
    0xde: u"Th", # LATIN CAPITAL LETTER THORN
    0xdf: u"ss", # LATIN SMALL LETTER SHARP S
    0xe6: u"ae", # LATIN SMALL LETTER AE
    0xf0: u"d",  # LATIN SMALL LETTER ETH
    0xf8: u"oe", # LATIN SMALL LETTER O WITH STROKE
    0xfe: u"th", # LATIN SMALL LETTER THORN
    }

'''
--------------------------------------------------
Chinese dictionary build - END
--------------------------------------------------
'''


def to_ranked_dict(lst):
    return dict((word, i) for i, word in enumerate(lst))

def filter_short(terms):
    '''
    only keep if brute-force possibilities are greater than this word's rank in the dictionary
    '''
    return [term for i, term in enumerate(terms) if 26**(len(term)) > i]

def filter_dup(lst, lists):
    '''
    filters lst to only include terms that don't have lower rank in another list
    '''
    max_rank = len(lst) + 1
    dct = to_ranked_dict(lst)
    dicts = [to_ranked_dict(l) for l in lists]
    return [word for word in lst if all(dct[word] < dct2.get(word, max_rank) for dct2 in dicts)]

def filter_ascii(lst):
    '''
    removes words with accent chars etc.
    (most accented words in the english lookup exist in the same table unaccented.)
    '''
    return [word for word in lst if all(ord(c) < 128 for c in word)]


def to_js(lst, lst_name):
    return 'var %s = %s;\n\n' % (lst_name, simplejson.dumps(lst))

'''
yaml files are needed for ruby gem
'''
def build_yaml(file_name, list_names, lsts):
	with open('../frequency_list.%s.yaml' % file_name, 'w') as f:
		f.write("---\n")
		for lst_name in list_names:
			lst = lsts[lst_name]
			for term in lst:
				f.write("- ")
				if term.isdigit():
					term = '"%s"' % term
				f.write(term)
				f.write("\n")

def main():
    english = get_ranked_english()
    surnames, male_names, female_names = get_ranked_census_names()
    passwords = get_ranked_common_passwords()

    [english,
     surnames, male_names, female_names,
     passwords] = [filter_ascii(filter_short(lst)) for lst in (english,
                                                               surnames, male_names, female_names,
                                                               passwords)]
    chinese = get_chinese_freq_words()
    chinese_surnames = get_chinese_surnames()
    chinese_names = get_chinese_names()

    # make dictionaries disjoint so that d1 & d2 == set() for any two dictionaries
    all_dicts = set(tuple(l) for l in [english, surnames, male_names, female_names, passwords, chinese, chinese_surnames, chinese_names])
    passwords    = filter_dup(passwords,    all_dicts - set([tuple(passwords)]))
    male_names   = filter_dup(male_names,   all_dicts - set([tuple(male_names)]))
    female_names = filter_dup(female_names, all_dicts - set([tuple(female_names)]))
    surnames     = filter_dup(surnames,     all_dicts - set([tuple(surnames)]))
    english      = filter_dup(english,      all_dicts - set([tuple(english)]))

    # remove this line in case of splitting dictionaries to separate files
    chinese      		= filter_dup(chinese,      		all_dicts - set([tuple(chinese)]))
    chinese_surnames 	= filter_dup(chinese_surnames, 	all_dicts - set([tuple(chinese_surnames)]))
    chinese_names 		= filter_dup(chinese_names, 	all_dicts - set([tuple(chinese_names)]))

    with open('../frequency_lists.js', 'w') as f: # words are all ascii at this point
        lsts = locals()
        for lst_name in 'passwords male_names female_names surnames english chinese chinese_surnames chinese_names'.split():
            lst = lsts[lst_name]
            f.write(to_js(lst, lst_name))

    build_yaml('english', 'passwords male_names female_names surnames english'.split(), lsts)
    build_yaml('chinese', 'chinese chinese_surnames chinese_names'.split(), lsts)

    print '\nall done! totals:\n'
    print 'passwords....', len(passwords)
    print 'male.........', len(male_names)
    print 'female.......', len(female_names)
    print 'surnames.....', len(surnames)
    print 'english......', len(english)
    print 'chinese......', len(chinese)
    print 'chinese_names......', len(chinese_names)
    print 'chinese_surnames......', len(chinese_surnames)

if __name__ == '__main__':
    if os.path.basename(os.getcwd()) != 'scripts':
        print 'run this from the scripts directory'
        exit(1)
    main()
