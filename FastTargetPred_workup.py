__version__ = "1.1"

from abc import ABC, abstractmethod
from pathlib import Path
from io import BytesIO
from urllib import request, error
from datetime import datetime
import base64
import re

import argparse
from csv import DictReader

class ARGUMENTS(object):
    CSV_INPUT = "i"
    SDF_INPUT = "sdf"
    HTML_OUTPUT = "o"
    SCORE_FILTER = "f"
    PLOT_STATS = "p"
    CLASS_NUMBER = "cn"
    SAVE_CHEMBL_STRUCT = "s"
    SPLIT_QUERY_COMPOUNDS = "c"
    ARG_LIST = [
        CSV_INPUT
        , SDF_INPUT
        , HTML_OUTPUT
        , SCORE_FILTER
        , PLOT_STATS
        , CLASS_NUMBER
        , SAVE_CHEMBL_STRUCT
        , SPLIT_QUERY_COMPOUNDS
    ]

HTM_LINK_TEMPLATE = """<a href="{link}" target="blank">{name}</a>"""

def render_classic_str(s: str, **kwargs): return s
def render_classic_float(s: str, **kwargs): return "{:0.02f}".format(float(s))
def render_query_mol(s: str, img_provider=None, **kwargs):
    if img_provider is None:
        return s
    else:
        return img_provider.get_img(s) + "<div>{}</div>".format(s)
def render_chembl_structure(s: str, arguments=None, **kwargs):
    url = "https://www.ebi.ac.uk/chembl/api/data/image/{}.svg".format(s)
    img_markup = ""
    if arguments is not None and arguments.get(ARGUMENTS.SAVE_CHEMBL_STRUCT, False):
        try :
            with request.urlopen(url, timeout=60) as response:
                response_bytes = response.read()
                b64_str = base64.b64encode(response_bytes).decode('ASCII')
                img_markup = f"<img src='data:image/png;base64,{b64_str}'/>"
        except error.URLError:
            print("CHEMBL topological formula fetching failed on {}".format(s))
    else:
        img_markup = f"<img src='{url.format(s)}'/>"


    base_url_template = "https://www.ebi.ac.uk/chembl/compound_report_card/{}/"

    s = re.sub(
        "CHEMBL[0-9]+"
        , lambda match : HTM_LINK_TEMPLATE.format(name=match.group(0), link=base_url_template.format(match.group(0)))
        , s
    )

    return "{}<div>{}</div>".format(img_markup, s)
def render_reactome_link(s: str, **kwargs):
    base_url_template = "https://reactome.org/PathwayBrowser/#/{}"
    s = re.sub(
        """ *(?P<reactome_id>[a-zA-Z]+-[a-zA-Z]+-(?P<reactome_number>[0-9]+)) *"""
        , lambda m: HTM_LINK_TEMPLATE.format(link=base_url_template.format(m.group("reactome_id")), name=m.group("reactome_number"))
        , s
    )
    s = s.replace(';', '</br>')
    return s

    return "</br>".join([HTM_LINK_TEMPLATE.format(link="https://reactome.org/PathwayBrowser/#/{}".format(x), name="Reactome") for x in s.split(";") if x != ""])
def render_gene_ontology(s: str, **kwargs):
    # Warning : char ':' must be translated to %3A for hotm query
    base_url_template = "http://amigo.geneontology.org/amigo/medial_search?q={}&searchtype=all"
    def get_markup(s):
        match = re.match(
            """(?P<name>[^\[\]]*) \[(?P<link>GO:[0-9]*)\]"""
            , s
        )
        if match:
            link = base_url_template.format(match.group("link").replace(":", "%3A"))
            return HTM_LINK_TEMPLATE.format(link=link, name=match.group('name'))
        else:
            return ""


    return "</br>".join([get_markup(x) for x in s.split(";")])
def render_involvement_in_disease(s: str, **kwargs):
    # format MIM strings
    base_url_template = "https://www.omim.org/entry/{}"
    s = re.sub(
        """(?P<disease_name>DISEASE:[^\[\]]*) (?P<mim_str>\[MIM:(?P<mim_num>[0-9]+)\])"""
        , lambda match: HTM_LINK_TEMPLATE.format(link=base_url_template.format(match.group("mim_num")), name=match.group("disease_name"))
        , s
    )

    # format PUBMED strings
    base_url_template = "https://www.ncbi.nlm.nih.gov/pubmed?cmd=search&term={}"
    s = re.sub(
        """PubMed:(?P<pubmed_num>[0-9]+)"""
        , lambda x:HTM_LINK_TEMPLATE.format(link=base_url_template.format(x.group("pubmed_num")), name="PubMed")
        , s
    )

    # format ECO strings
    base_url_template = "https://www.ebi.ac.uk/QuickGO/term/{}"
    s = re.sub(
        """(?<!/)(?P<eco_num>ECO:[0-9]+)(?!")"""
        ,  lambda x:(HTM_LINK_TEMPLATE.format(link=base_url_template.format(x.group("eco_num")), name="ECO"))
        , s
    )


    return s
def render_chembl_target(s: str, **kwargs):
    base_url_template = "https://www.ebi.ac.uk/chembl/target_report_card/{}/"
    s = re.sub(
        "CHEMBL[0-9]+"
        , lambda match : HTM_LINK_TEMPLATE.format(name=match.group(0), link=base_url_template.format(match.group(0)))
        , s
    )
    return s
def render_uniprot_id(s: str, **kwargs):
    base_url_template = "https://www.uniprot.org/uniprot/{}"
    s = re.sub(
        "(?P<uniprot_id>.*)"
        , lambda match : HTM_LINK_TEMPLATE.format(name=match.group('uniprot_id'), link=base_url_template.format(match.group('uniprot_id')))
        , s
    )
    return s


class CSVFIELDS(object):
    query_name = "query_name"
    database_molecule_id = "database_molecule_id"
    target_id = "target_id"
    score = "score"
    Entry = "Uniprot"
    Entry_name = "Uniprot name"
    Status = "Status"
    Protein_names = "Protein names"
    Gene_names = "Gene names"
    Organism = "Organism"
    CHEMBL = "CHEMBL"
    Involvement_in_disease = "Involvement in disease"
    Gene_ontology = "Gene ontology (biological process)"
    Reactome = "Cross-reference (Reactome)"
    field_list = (
        query_name
        , database_molecule_id
        # , target_id  # This one is quite useless actually
        , score
        , Entry
        , Entry_name
        , Status
        , Protein_names
        , Gene_names
        , Organism
        , CHEMBL
        , Involvement_in_disease
        , Gene_ontology
        , Reactome
    )
    field_display_function = {
        query_name: render_query_mol
        # query_name: render_classic_str
        , database_molecule_id: render_chembl_structure
        # , database_molecule_id: render_classic_str
        , target_id: render_classic_str
        , score: render_classic_float
        , Entry: render_uniprot_id
        , Entry_name: render_classic_str
        , Status: render_classic_str
        , Protein_names: render_classic_str
        , Gene_names: render_classic_str
        , Organism: render_classic_str
        , CHEMBL: render_chembl_target
        , Involvement_in_disease: render_involvement_in_disease
        , Gene_ontology: render_gene_ontology
        , Reactome: render_reactome_link
    }


def read_file(file_name: str) -> list:
    print("Reading csv file ...")
    file = Path(file_name)
    if not file.is_file():
        raise FileNotFoundError

    l = []
    with file.open('r') as f:
        reader = DictReader(f, delimiter="\t")
        for row in reader:
            l.append({field: row.get(field, None) for field in CSVFIELDS.field_list})

    return sorted(l, key=(lambda x: x[CSVFIELDS.score]), reverse=True)


def get_header():
    css = """<head>
    <style>
html {
  font-family: Helvetica;
}

h1 {
  text-align: center;
  font-size:46;
  color:#55C;
  text-shadow: 0 0 1px #88F;
}
table {
    border-collapse: collapse;
    
}
td {
    position: relative;
    border: solid 1px #AAA;
    padding-left:5px;
    padding-right:5px;
    text-align: center;
}
th {
  cursor:pointer;
}

td img {
    height: auto;
    width: 250px;
}
table.tablestyle-1  {
  border-collapse: collapse;
}

table.tablestyle-1 td,table.tablestyle-1 th {
  padding:8px;
  border: 1px solid white;
}


table.tablestyle-1 tbody>*:nth-child(2n) td {
  background-color: #CFC;
}

table.tablestyle-1 tbody td {
  background-color: #DFD;
}

table.tablestyle-1 thead th{
  font-weight: bold;
  background-color: #CCF;
}

table.tablestyle-1 thead th:first-child {
  border-top-left-radius:10px;
}

table.tablestyle-1 thead th:last-child {
  border-top-right-radius:10px;
}

table.tablestyle-1 tbody>*:last-child td:first-child {
  border-bottom-left-radius:10px;
}

table.tablestyle-1 tbody>*:last-child td:last-child {
  border-bottom-right-radius:10px;
}
    
.info-box {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  
}
    
    
    </style>"""
    js = """
    <script>
/*
  SortTable
  version 2
  7th April 2007
  Stuart Langridge, http://www.kryogenix.org/code/browser/sorttable/
  
*/


var stIsIE = /*@cc_on!@*/false;

sorttable = {
  init: function() {
    // quit if this function has already been called
    if (arguments.callee.done) return;
    // flag this function so we don't do the same thing twice
    arguments.callee.done = true;
    // kill the timer
    if (_timer) clearInterval(_timer);

    if (!document.createElement || !document.getElementsByTagName) return;

    sorttable.DATE_RE = /^(\\d\\d?)[\\/\\.-](\\d\\d?)[\\/\\.-]((\\d\\d)?\\d\\d)$/;

    forEach(document.getElementsByTagName('table'), function(table) {
      if (table.className.search(/\\bsortable\\b/) != -1) {
        sorttable.makeSortable(table);
      }
    });

  },

  makeSortable: function(table) {
    if (table.getElementsByTagName('thead').length == 0) {
      // table doesn't have a tHead. Since it should have, create one and
      // put the first table row in it.
      the = document.createElement('thead');
      the.appendChild(table.rows[0]);
      table.insertBefore(the,table.firstChild);
    }
    // Safari doesn't support table.tHead, sigh
    if (table.tHead == null) table.tHead = table.getElementsByTagName('thead')[0];

    if (table.tHead.rows.length != 1) return; // can't cope with two header rows

    // Sorttable v1 put rows with a class of "sortbottom" at the bottom (as
    // "total" rows, for example). This is B&R, since what you're supposed
    // to do is put them in a tfoot. So, if there are sortbottom rows,
    // for backwards compatibility, move them to tfoot (creating it if needed).
    sortbottomrows = [];
    for (var i=0; i<table.rows.length; i++) {
      if (table.rows[i].className.search(/\\bsortbottom\\b/) != -1) {
        sortbottomrows[sortbottomrows.length] = table.rows[i];
      }
    }
    if (sortbottomrows) {
      if (table.tFoot == null) {
        // table doesn't have a tfoot. Create one.
        tfo = document.createElement('tfoot');
        table.appendChild(tfo);
      }
      for (var i=0; i<sortbottomrows.length; i++) {
        tfo.appendChild(sortbottomrows[i]);
      }
      delete sortbottomrows;
    }

    // work through each column and calculate its type
    headrow = table.tHead.rows[0].cells;
    for (var i=0; i<headrow.length; i++) {
      // manually override the type with a sorttable_type attribute
      if (!headrow[i].className.match(/\\bsorttable_nosort\\b/)) { // skip this col
        mtch = headrow[i].className.match(/\\bsorttable_([a-z0-9]+)\\b/);
        if (mtch) { override = mtch[1]; }
	      if (mtch && typeof sorttable["sort_"+override] == 'function') {
	        headrow[i].sorttable_sortfunction = sorttable["sort_"+override];
	      } else {
	        headrow[i].sorttable_sortfunction = sorttable.guessType(table,i);
	      }
	      // make it clickable to sort
	      headrow[i].sorttable_columnindex = i;
	      headrow[i].sorttable_tbody = table.tBodies[0];
	      dean_addEvent(headrow[i],"click", sorttable.innerSortFunction = function(e) {

          if (this.className.search(/\\bsorttable_sorted\\b/) != -1) {
            // if we're already sorted by this column, just
            // reverse the table, which is quicker
            sorttable.reverse(this.sorttable_tbody);
            this.className = this.className.replace('sorttable_sorted',
                                                    'sorttable_sorted_reverse');
            this.removeChild(document.getElementById('sorttable_sortfwdind'));
            sortrevind = document.createElement('span');
            sortrevind.id = "sorttable_sortrevind";
            sortrevind.innerHTML = stIsIE ? '&nbsp<font face="webdings">5</font>' : '&nbsp;&#x25B4;';
            this.appendChild(sortrevind);
            return;
          }
          if (this.className.search(/\\bsorttable_sorted_reverse\\b/) != -1) {
            // if we're already sorted by this column in reverse, just
            // re-reverse the table, which is quicker
            sorttable.reverse(this.sorttable_tbody);
            this.className = this.className.replace('sorttable_sorted_reverse',
                                                    'sorttable_sorted');
            this.removeChild(document.getElementById('sorttable_sortrevind'));
            sortfwdind = document.createElement('span');
            sortfwdind.id = "sorttable_sortfwdind";
            sortfwdind.innerHTML = stIsIE ? '&nbsp<font face="webdings">6</font>' : '&nbsp;&#x25BE;';
            this.appendChild(sortfwdind);
            return;
          }

          // remove sorttable_sorted classes
          theadrow = this.parentNode;
          forEach(theadrow.childNodes, function(cell) {
            if (cell.nodeType == 1) { // an element
              cell.className = cell.className.replace('sorttable_sorted_reverse','');
              cell.className = cell.className.replace('sorttable_sorted','');
            }
          });
          sortfwdind = document.getElementById('sorttable_sortfwdind');
          if (sortfwdind) { sortfwdind.parentNode.removeChild(sortfwdind); }
          sortrevind = document.getElementById('sorttable_sortrevind');
          if (sortrevind) { sortrevind.parentNode.removeChild(sortrevind); }

          this.className += ' sorttable_sorted';
          sortfwdind = document.createElement('span');
          sortfwdind.id = "sorttable_sortfwdind";
          sortfwdind.innerHTML = stIsIE ? '&nbsp<font face="webdings">6</font>' : '&nbsp;&#x25BE;';
          this.appendChild(sortfwdind);

	        // build an array to sort. This is a Schwartzian transform thing,
	        // i.e., we "decorate" each row with the actual sort key,
	        // sort based on the sort keys, and then put the rows back in order
	        // which is a lot faster because you only do getInnerText once per row
	        row_array = [];
	        col = this.sorttable_columnindex;
	        rows = this.sorttable_tbody.rows;
	        for (var j=0; j<rows.length; j++) {
	          row_array[row_array.length] = [sorttable.getInnerText(rows[j].cells[col]), rows[j]];
	        }
	        /* If you want a stable sort, uncomment the following line */
	        //sorttable.shaker_sort(row_array, this.sorttable_sortfunction);
	        /* and comment out this one */
	        row_array.sort(this.sorttable_sortfunction);

	        tb = this.sorttable_tbody;
	        for (var j=0; j<row_array.length; j++) {
	          tb.appendChild(row_array[j][1]);
	        }

	        delete row_array;
	      });
	    }
    }
  },

  guessType: function(table, column) {
    // guess the type of a column based on its first non-blank row
    sortfn = sorttable.sort_alpha;
    for (var i=0; i<table.tBodies[0].rows.length; i++) {
      text = sorttable.getInnerText(table.tBodies[0].rows[i].cells[column]);
      if (text != '') {
        if (text.match(/^-?[£$¤]?[\\d,.]+%?$/)) {
          return sorttable.sort_numeric;
        }
        // check for a date: dd/mm/yyyy or dd/mm/yy
        // can have / or . or - as separator
        // can be mm/dd as well
        possdate = text.match(sorttable.DATE_RE)
        if (possdate) {
          // looks like a date
          first = parseInt(possdate[1]);
          second = parseInt(possdate[2]);
          if (first > 12) {
            // definitely dd/mm
            return sorttable.sort_ddmm;
          } else if (second > 12) {
            return sorttable.sort_mmdd;
          } else {
            // looks like a date, but we can't tell which, so assume
            // that it's dd/mm (English imperialism!) and keep looking
            sortfn = sorttable.sort_ddmm;
          }
        }
      }
    }
    return sortfn;
  },

  getInnerText: function(node) {
    // gets the text we want to use for sorting for a cell.
    // strips leading and trailing whitespace.
    // this is *not* a generic getInnerText function; it's special to sorttable.
    // for example, you can override the cell text with a customkey attribute.
    // it also gets .value for <input> fields.

    if (!node) return "";

    hasInputs = (typeof node.getElementsByTagName == 'function') &&
                 node.getElementsByTagName('input').length;

    if (node.getAttribute("sorttable_customkey") != null) {
      return node.getAttribute("sorttable_customkey");
    }
    else if (typeof node.textContent != 'undefined' && !hasInputs) {
      return node.textContent.replace(/^\\s+|\\s+$/g, '');
    }
    else if (typeof node.innerText != 'undefined' && !hasInputs) {
      return node.innerText.replace(/^\\s+|\\s+$/g, '');
    }
    else if (typeof node.text != 'undefined' && !hasInputs) {
      return node.text.replace(/^\\s+|\\s+$/g, '');
    }
    else {
      switch (node.nodeType) {
        case 3:
          if (node.nodeName.toLowerCase() == 'input') {
            return node.value.replace(/^\\s+|\\s+$/g, '');
          }
        case 4:
          return node.nodeValue.replace(/^\\s+|\\s+$/g, '');
          break;
        case 1:
        case 11:
          var innerText = '';
          for (var i = 0; i < node.childNodes.length; i++) {
            innerText += sorttable.getInnerText(node.childNodes[i]);
          }
          return innerText.replace(/^\\s+|\\s+$/g, '');
          break;
        default:
          return '';
      }
    }
  },

  reverse: function(tbody) {
    // reverse the rows in a tbody
    newrows = [];
    for (var i=0; i<tbody.rows.length; i++) {
      newrows[newrows.length] = tbody.rows[i];
    }
    for (var i=newrows.length-1; i>=0; i--) {
       tbody.appendChild(newrows[i]);
    }
    delete newrows;
  },

  /* sort functions
     each sort function takes two parameters, a and b
     you are comparing a[0] and b[0] */
  sort_numeric: function(a,b) {
    aa = parseFloat(a[0].replace(/[^0-9.-]/g,''));
    if (isNaN(aa)) aa = 0;
    bb = parseFloat(b[0].replace(/[^0-9.-]/g,''));
    if (isNaN(bb)) bb = 0;
    return aa-bb;
  },
  sort_alpha: function(a,b) {
    if (a[0]==b[0]) return 0;
    if (a[0]<b[0]) return -1;
    return 1;
  },
  sort_ddmm: function(a,b) {
    mtch = a[0].match(sorttable.DATE_RE);
    y = mtch[3]; m = mtch[2]; d = mtch[1];
    if (m.length == 1) m = '0'+m;
    if (d.length == 1) d = '0'+d;
    dt1 = y+m+d;
    mtch = b[0].match(sorttable.DATE_RE);
    y = mtch[3]; m = mtch[2]; d = mtch[1];
    if (m.length == 1) m = '0'+m;
    if (d.length == 1) d = '0'+d;
    dt2 = y+m+d;
    if (dt1==dt2) return 0;
    if (dt1<dt2) return -1;
    return 1;
  },
  sort_mmdd: function(a,b) {
    mtch = a[0].match(sorttable.DATE_RE);
    y = mtch[3]; d = mtch[2]; m = mtch[1];
    if (m.length == 1) m = '0'+m;
    if (d.length == 1) d = '0'+d;
    dt1 = y+m+d;
    mtch = b[0].match(sorttable.DATE_RE);
    y = mtch[3]; d = mtch[2]; m = mtch[1];
    if (m.length == 1) m = '0'+m;
    if (d.length == 1) d = '0'+d;
    dt2 = y+m+d;
    if (dt1==dt2) return 0;
    if (dt1<dt2) return -1;
    return 1;
  },

  shaker_sort: function(list, comp_func) {
    // A stable sort function to allow multi-level sorting of data
    // see: http://en.wikipedia.org/wiki/Cocktail_sort
    // thanks to Joseph Nahmias
    var b = 0;
    var t = list.length - 1;
    var swap = true;

    while(swap) {
        swap = false;
        for(var i = b; i < t; ++i) {
            if ( comp_func(list[i], list[i+1]) > 0 ) {
                var q = list[i]; list[i] = list[i+1]; list[i+1] = q;
                swap = true;
            }
        } // for
        t--;

        if (!swap) break;

        for(var i = t; i > b; --i) {
            if ( comp_func(list[i], list[i-1]) < 0 ) {
                var q = list[i]; list[i] = list[i-1]; list[i-1] = q;
                swap = true;
            }
        } // for
        b++;

    } // while(swap)
  }
}

/* ******************************************************************
   Supporting functions: bundled here to avoid depending on a library
   ****************************************************************** */

// Dean Edwards/Matthias Miller/John Resig

/* for Mozilla/Opera9 */
if (document.addEventListener) {
    document.addEventListener("DOMContentLoaded", sorttable.init, false);
}

/* for Internet Explorer */
/*@cc_on @*/
/*@if (@_win32)
    document.write("<script id=__ie_onload defer src=javascript:void(0)><\\/script>");
    var script = document.getElementById("__ie_onload");
    script.onreadystatechange = function() {
        if (this.readyState == "complete") {
            sorttable.init(); // call the onload handler
        }
    };
/*@end @*/

/* for Safari */
if (/WebKit/i.test(navigator.userAgent)) { // sniff
    var _timer = setInterval(function() {
        if (/loaded|complete/.test(document.readyState)) {
            sorttable.init(); // call the onload handler
        }
    }, 10);
}

/* for other browsers */
window.onload = sorttable.init;

// written by Dean Edwards, 2005
// with input from Tino Zijdel, Matthias Miller, Diego Perini

// http://dean.edwards.name/weblog/2005/10/add-event/

function dean_addEvent(element, type, handler) {
	if (element.addEventListener) {
		element.addEventListener(type, handler, false);
	} else {
		// assign each event handler a unique ID
		if (!handler.$$guid) handler.$$guid = dean_addEvent.guid++;
		// create a hash table of event types for the element
		if (!element.events) element.events = {};
		// create a hash table of event handlers for each element/event pair
		var handlers = element.events[type];
		if (!handlers) {
			handlers = element.events[type] = {};
			// store the existing event handler (if there is one)
			if (element["on" + type]) {
				handlers[0] = element["on" + type];
			}
		}
		// store the event handler in the hash table
		handlers[handler.$$guid] = handler;
		// assign a global event handler to do all the work
		element["on" + type] = handleEvent;
	}
};
// a counter used to create unique IDs
dean_addEvent.guid = 1;

function removeEvent(element, type, handler) {
	if (element.removeEventListener) {
		element.removeEventListener(type, handler, false);
	} else {
		// delete the event handler from the hash table
		if (element.events && element.events[type]) {
			delete element.events[type][handler.$$guid];
		}
	}
};

function handleEvent(event) {
	var returnValue = true;
	// grab the event object (IE uses a global event object)
	event = event || fixEvent(((this.ownerDocument || this.document || this).parentWindow || window).event);
	// get a reference to the hash table of event handlers
	var handlers = this.events[event.type];
	// execute each event handler
	for (var i in handlers) {
		this.$$handleEvent = handlers[i];
		if (this.$$handleEvent(event) === false) {
			returnValue = false;
		}
	}
	return returnValue;
};

function fixEvent(event) {
	// add W3C standard event methods
	event.preventDefault = fixEvent.preventDefault;
	event.stopPropagation = fixEvent.stopPropagation;
	return event;
};
fixEvent.preventDefault = function() {
	this.returnValue = false;
};
fixEvent.stopPropagation = function() {
  this.cancelBubble = true;
}

// Dean's forEach: http://dean.edwards.name/base/forEach.js
/*
	forEach, version 1.0
	Copyright 2006, Dean Edwards
	License: http://www.opensource.org/licenses/mit-license.php
*/

// array-like enumeration
if (!Array.forEach) { // mozilla already supports this
	Array.forEach = function(array, block, context) {
		for (var i = 0; i < array.length; i++) {
			block.call(context, array[i], i, array);
		}
	};
}

// generic enumeration
Function.prototype.forEach = function(object, block, context) {
	for (var key in object) {
		if (typeof this.prototype[key] == "undefined") {
			block.call(context, object[key], key, object);
		}
	}
};

// character enumeration
String.forEach = function(string, block, context) {
	Array.forEach(string.split(""), function(chr, index) {
		block.call(context, chr, index, string);
	});
};

// globally resolve forEach enumeration
var forEach = function(object, block, context) {
	if (object) {
		var resolve = Object; // default
		if (object instanceof Function) {
			// functions have a "length" property
			resolve = Function;
		} else if (object.forEach instanceof Function) {
			// the object implements a custom forEach method so use that
			object.forEach(block, context);
			return;
		} else if (typeof object == "string") {
			// the object is a string
			resolve = String;
		} else if (typeof object.length == "number") {
			// the object is array-like
			resolve = Array;
		}
		resolve.forEach(object, block, context);
	}
};


    </script>
    </head>"""
    return css + js


def get_info(row_list, arguments):
    stats = ""
    if arguments[ARGUMENTS.PLOT_STATS]:
        stats = get_plot_stats(row_list, arguments)

    field_description = ""

    info_html = """
    <div class="info-box">
    {field_description}
    {stats}
    </div>
    """.format(stats=stats, field_description=field_description)
    return info_html


def filter_rows(row_list, arguments):
    if arguments[ARGUMENTS.SCORE_FILTER]:
        print("Filtering score smaller than {} ...".format(arguments[ARGUMENTS.SCORE_FILTER]))
        assert isinstance(arguments[ARGUMENTS.SCORE_FILTER], float)
        num_field = 0
        for i, row in enumerate(row_list):
            if float(row[CSVFIELDS.score]) < arguments[ARGUMENTS.SCORE_FILTER]:
                num_field = i - 1
                break

        return row_list[:num_field + 1]
    else:
        return row_list


class WriteManager(ABC):
    def __init__(self,arguments):
        self.file = Path(arguments[ARGUMENTS.HTML_OUTPUT])
        self.arguments = arguments
        self._beginning = "<html>"
        self._header = get_header()
        self._title = """<h1>Results from {}</h1>"""
        self._info = ""
        self._end = "</body></html>"
        self.write_function_kwarg = {"arguments": self.arguments}
        if self.arguments[ARGUMENTS.SDF_INPUT] is not None:
            print("Reading SD File ...")
            self.write_function_kwarg["img_provider"] = ImageProvider()

    @abstractmethod
    def write_header(self): pass

    @abstractmethod
    def write_title(self): pass

    @abstractmethod
    def write_info(self, row_list): pass

    @abstractmethod
    def write_body(self, row_list): pass

    @abstractmethod
    def write_end(self): pass


class WriteManager1(WriteManager):
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self.f = open(str(self.file), 'w')
        self.f.write(self._beginning)

    def write_header(self):
        self.f.write(self._header)
        self.f.write("<body>")

    def write_title(self):
        self.f.write(self._title.format(Path(self.arguments[ARGUMENTS.CSV_INPUT])))

    def write_info(self, row_list):
        self._info = get_info(row_list, self.arguments)
        self.f.write(self._info)

    def write_body(self, row_list):
        field_htm = "<td>{}</td>"
        row_htm = "<tr>{}</tr>"
        self.f.write("""<table class="tablestyle-1 sortable">""")

        self.f.write("<thead>")
        s_temp2 = ""
        for field in CSVFIELDS.field_list:
            s_temp2 += "<th>{}</th>".format(field)
        self.f.write(row_htm.format(s_temp2))
        self.f.write("</thead><tbody>")

        if self.arguments.get(ARGUMENTS.SAVE_CHEMBL_STRUCT, False):
            print("Querying Chembl server to retrieve structures. This step might be long ...")
        else:
            print("Writing results table ...")

        for row in row_list:
            s_temp1 = ""
            for field in CSVFIELDS.field_list:
                s_temp1 += field_htm.format(CSVFIELDS.field_display_function[field](row[field], **self.write_function_kwarg))
            self.f.write(row_htm.format(s_temp1))

        self.f.write("</tbody>")
        self.f.write("</table>")

    def write_end(self):
        self.f.write(self._end)
        self.f.close()


class WriteManager2(WriteManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._title = """<h1>Results for query compound {}</h1>"""
        self._template = ["", "", ""]

    def write_header(self):
        self._template[0] += self._header
        self._template[0] += "<body>"

    def write_title(self):
        self._template[0] += self._title.split("{}")[0]
        self._template[1] += self._title.split("{}")[1]

    def write_info(self, row_list):
        self._info = get_info(row_list, self.arguments)
        self._template[1] += self._info

        row_htm = "<tr>{}</tr>"

        self._template[1] += """<table class="tablestyle-1 sortable">"""

        self._template[1] += "<thead>"
        s_temp2 = ""
        for field in CSVFIELDS.field_list:
            s_temp2 += "<th>{}</th>".format(field)
        self._template[1] += (row_htm.format(s_temp2))
        self._template[1] += "</thead><tbody>"
        self._template[2] += "</tbody>"
        self._template[2] += "</table>"

        self._template[2] += self._end

    def write_body(self, row_list):
        field_htm = "<td>{}</td>"
        row_htm = "<tr>{}</tr>"
        # Gather data per query molecule
        query_compound_dict = {}
        for row in row_list:
            current_qc = row[CSVFIELDS.query_name]
            if current_qc not in query_compound_dict:
                query_compound_dict[current_qc] = []
            query_compound_dict[current_qc].append(row)

        # Now write one file per molecule
        html_pseudofile = Path(self.arguments[ARGUMENTS.HTML_OUTPUT])
        dir = Path(html_pseudofile.parent, html_pseudofile.stem)
        if dir.exists() and not dir.is_dir():
            raise FileExistsError("Attempted to create folder named {} but name already taken.".format(dir))
        elif not dir.exists():
            dir.mkdir()

        for query_compound_name, compound_row_list in query_compound_dict.items():
            file = Path(dir, query_compound_name + ".html")
            print(f"Writing {str(file)} ...")
            table_body = ""
            for row in compound_row_list:
                s_temp1 = ""
                for field in CSVFIELDS.field_list:
                    s_temp1 += field_htm.format(
                        CSVFIELDS.field_display_function[field](row[field], **self.write_function_kwarg))
                table_body += row_htm.format(s_temp1)

            file.write_text(
                self._template[0] + query_compound_name + self._template[1] + table_body + self._template[2]
            )

    def write_end(self):
        pass


def main(arguments: dict):
    row_list = read_file(arguments[ARGUMENTS.CSV_INPUT])

    if arguments[ARGUMENTS.SPLIT_QUERY_COMPOUNDS] is True:
        f = WriteManager2(arguments)
    else:
        f = WriteManager1(arguments)

    f.write_header()

    f.write_title()

    f.write_info(row_list)

    filtered_row_list = filter_rows(row_list, arguments)

    f.write_body(filtered_row_list)

    f.write_end()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script version {}. Will process csv ouptut from FastTargetPred to build a single html file.".format(__version__))
    mandatory_arguments = parser.add_argument_group(title="Mandatory arguments")
    mandatory_arguments.add_argument(f"-{ARGUMENTS.CSV_INPUT}", help="Path to the output csv file of FastTargetPred.")
    mandatory_arguments.add_argument(f"-{ARGUMENTS.HTML_OUTPUT}", help="Path to the HTML report.", default="out_{}.html".format(datetime.now().isoformat().replace(':',' ')))
    optional_arguments = parser.add_argument_group(title="Additional arguments")
    optional_arguments.add_argument(f"-{ARGUMENTS.SDF_INPUT}", help="Path to the SD file used as input of FastTargetPred. Used for image generation.\nWarning : RDKit is required for this to work.")
    optional_arguments.add_argument(f"-{ARGUMENTS.SCORE_FILTER}", help="Score Filtering value.\nUsefull if you want a smaller or cleaner file.", type=float)
    optional_arguments.add_argument(f"-{ARGUMENTS.PLOT_STATS}", help="Will analyse data and plot a few metrics at the top of the html report.", action='store_true')
    # optional_arguments.add_argument(f"-{ARGUMENTS.SAVE_CHEMBL_STRUCT}", help="Save Chembl molecule structure into the output file.\nWill take longer to create and will create a bigger file, but allow offline consultation.", action='store_true')
    optional_arguments.add_argument(f"-{ARGUMENTS.CLASS_NUMBER}", help="Class Number.\nWill change the frequency distribution graph class width in order to have the desired number of class.", type=int, default=20)
    optional_arguments.add_argument(f"-{ARGUMENTS.SPLIT_QUERY_COMPOUNDS}", help="Split Query Compounds.\nWill generate one file per query compound and put them all in a folder named after your seleted output.", action='store_true')

    namespace = parser.parse_args()
    argument_dict = {arg:namespace.__getattribute__(arg)  for arg in ARGUMENTS.ARG_LIST if hasattr(namespace, arg)}

    if argument_dict[ARGUMENTS.SDF_INPUT]:
        try:
            from rdkit import Chem
            from rdkit.Chem.Draw import MolToImage
            from rdkit.Chem.Draw.MolDrawing import DrawingOptions
            from rdkit.Chem.Draw import rdMolDraw2D
            d2d = rdMolDraw2D.MolDraw2DCairo(300, 300)
            opts = d2d.drawOptions()
            opts.clearBackground = False

            class ImageProvider(object):
                def __init__(self):
                    self.image_dict = {}
                    molsup = Chem.SDMolSupplier(argument_dict[ARGUMENTS.SDF_INPUT])
                    for mol in molsup:
                        if mol:
                            name = mol.GetProp('_Name')
                            if name not in self.image_dict:
                                self.image_dict[name] = self._get_img_html_markup(mol)

                def _get_img_html_markup(self, mol) -> str:
                    d2d = rdMolDraw2D.MolDraw2DCairo(300, 300)
                    opts = d2d.drawOptions()
                    opts.clearBackground = False
                    d2d.DrawMolecule(mol)
                    d2d.FinishDrawing()
                    im_data = d2d.GetDrawingText()
                    b64_str = base64.b64encode(im_data).decode()
                    data_url = 'data:image/png;base64,' + b64_str
                    htm = """<img src="{}"/> """.format(data_url)
                    return htm

                def _get_empty_img_html_markup(self, name: str):
                    return """<div>{}</div>""".format(name)

                def get_img(self, mol_name: str):
                    if mol_name in self.image_dict:
                        return self.image_dict[mol_name]
                    else:
                        return self._get_empty_img_html_markup(mol_name)

        except ModuleNotFoundError:
            print("It appears you don't have Rdkit and Pycairo installed. Printing query structure will only work with these.")
            class ImageProvider(object):
                def get_img(self, s): return ""

    if argument_dict[ARGUMENTS.PLOT_STATS]:
        try:
            import numpy as np
            from matplotlib.figure import Figure
            from matplotlib.text import Text
            from statistics import mean
        except ModuleNotFoundError:
            print("It appears you don't have Numpy and Matplotlib installed. Printing stats will only work with it.")
            exit()

        def get_plot_stats(row_list, arguments):
            print("Plotting data statistics ...")
            score_array = np.array([float(x[CSVFIELDS.score]) for x in row_list])

            fig = Figure()
            ax = fig.subplots()
            buf = BytesIO()

            ax.hist(score_array, bins=arguments[ARGUMENTS.CLASS_NUMBER])
            ax.set_title('Hits score distribution')
            ax.set_ylabel("Hit count")
            ax.set_xlabel("Score")
            if arguments[ARGUMENTS.SCORE_FILTER]:  # In case a threshold value has been specified, show where it cut the data
                y_lim = ax.get_ylim()
                ax.set_ylim(y_lim)
                ax.plot((arguments[ARGUMENTS.SCORE_FILTER], arguments[ARGUMENTS.SCORE_FILTER]), y_lim)
                ax.annotate(
                    "Filter\nthreshold"
                    , xy=(arguments[ARGUMENTS.SCORE_FILTER], y_lim[1]*0.7)
                    , xytext=(arguments[ARGUMENTS.SCORE_FILTER]*1.05, 0.9*y_lim[1])
                    , arrowprops=dict(facecolor='black', shrink=0.05)
                    , horizontalalignment='left'
                    , verticalalignment='center'
                )

            fig.savefig(buf, format="png")
            data = base64.b64encode(buf.getbuffer()).decode("ascii")
            html_str = f"<div class='stats'><img src='data:image/png;base64,{data}'/></div>"
            return html_str



    main(argument_dict)
