# -*- coding: utf-8 -*-

getPartialXPath = """
function getFullXPath(node, option) {
  try {
    var d = node.ownerDocument;
    var option = option||{};
    var xpath = '';
    var xtext = [];

    var gettext = function(e, desctext) {
      try {
        if(!e) return [];
        var hash = {};
        for(var i=0; i<desctext.length; i++) {
          hash[desctext[i]] = 1;
        }
        var buf = {};
        var gettext1 = function(a) {
          switch(a.nodeType) {
            case 1:
            if(!a.nodeName.match(/^(?:HTML|BODY|SCRIPT|STYLE)$/)) {
              for(var i=0; i<a.childNodes.length; i++) {
                gettext1(a.childNodes[i]);
              }
            }
            break;
            case 3:
            var t = a.nodeValue.split(/[\\r\\n\\'\\"\\[\\]]/);
            for(var i=0; i<t.length; i++) {
              var s = t[i];
              s = s.replace(/^\\s+/,'');
              s = s.replace(/\\s+$/,'');
              if(s && !s.match(/^[0-9]+$/)) {
                s = '[contains(.,' + tostring(s) + ')]';
                buf[s] = 1;
              }
            }
            break;
          }
        }
        gettext1(e);
        var text = [];
        for(var s in buf) {
          if(hash[s]==undefined) text.push(s);
        }
        return text.sort();
      } catch(e) {
        alert(e);
      }
    };
    var getattr = function(e) {
      try {
        if(!e) return [];
        var attr = [];
        var getattr1 = function(a) {
          if(a.nodeName.indexOf('on') != 0 && a.nodeName.indexOf(':') == -1 && a.nodeName.match(/^[\\x20-\\x7f]+$/)) {
            if(a.nodeName == 'class') {
              var aa = a.nodeValue.split(/[\\s\\r\\n]+/);
              for(var j=0; j<aa.length; j++) {
                if(aa[j]) {
                  attr.push('[contains(@' + a.nodeName + ',' + tostring(aa[j]) + ')]');
                }
              }
            } else {
              var aa = a.nodeValue.split(/[\\r\\n]/);
              if(aa.length == 1) {
                attr.push('[@' + a.nodeName + '=' + tostring(aa[0]) + ']');
              } else {
                attr.push('[starts-with(@' + a.nodeName + ',' + tostring(aa[0]) + ')]');
              }
            }
          }
        }
        switch(e.nodeType) {
          case 1:
          for(var i=0; i<e.attributes.length; i++) {
            getattr1(e.attributes[i]);
          }
          break;
          case 2:
          getattr1(e);
          break;
        }
        return attr.sort();
      } catch(e) {
        alert(e);
      }
    };
    var tostring = function(s) {
      try {
        var str = '';
        var quot = s.indexOf("'") > -1 ? '"' : "'";
        if(s && s.match(/--/)) {
          var a = s.split(/--/);
          a[0] = quot + a[0] + '-' + quot;
          for(var i=1; i<a.length-1; i++) {
            a[i] = quot + '-' + a[i] + '-' + quot;
          }
          a[a.length-1] = quot + '-' + a[a.length-1] + quot;
          str = 'concat(' + a.join(',') + ')';
        } else if(s && s.match(/[\\[\\]]/)) {
          var t = s.replace(/\\]/g,'--]--').replace(/\\[/g,'--[--').replace(/----/g,'--');
          var a = t.split(/--/);
          for(var i=0; i<a.length; i++) {
            a[i] = quot + a[i] + quot;
          }
          str = 'concat(' + a.join(',') + ')';
        } else {
          str = quot + s + quot;
        }
        return str;
      } catch(e) {
        alert(e);
      }
    };
    var match = function(a, b) {
      //a=比較対象
      //b=ルール
      try {
        var c = {};
        for(var i=0; i<a.length; i++) {
          c[a[i]] = 1;
        }
        for(var i=0; i<b.length; i++) {
          if(c[b[i]] == undefined) return false;
        }
        return true;
      } catch(e) {
        alert(e);
      }
    };

    while(node) {
      var pnode = node.parentNode;
      var nname = node.nodeName.toLowerCase();
      if(node.nodeName.indexOf(':') > -1) {
        //*[name()='CAKE:NOCACHE' or name()='nocache']
        nname = "*[name()='" + node.nodeName.toUpperCase() + "' or name()='" + node.nodeName.split(':')[1].toLowerCase() + "']";
      }
      if(pnode) {
        if(option.attributes == 4) {
          //全textノード、全attributeノードを条件として設定する
          var attr0 = getattr(node);
          var text0 = gettext(node,xtext);
          for(var i=0, j=1; pnode.childNodes[i]; i++){
            var e = pnode.childNodes[i];
            if(e.nodeType == 1) {
              var attr1 = getattr(e);
              var text1 = gettext(e,xtext);
              if(e.nodeName == node.nodeName && match(attr1,attr0) && match(text1,text0)) {
                if(e == node) {
                  var index = option.noindex ? '' : '[' + j + ']';
                  xpath = '/' + nname + attr0.join('') + text0.join('') + index + xpath;
                  xtext = xtext.concat(text0);
                  break;
                }
                j++;
              }
            }
          }
        } else if(option.attributes == 3) {
          //全attributeノードを条件として設定する
          var attr0 = getattr(node);
          for(var i=0, j=1; pnode.childNodes[i]; i++){
            var e = pnode.childNodes[i];
            if(e.nodeType == 1) {
              var attr1 = getattr(e);
              if(e.nodeName == node.nodeName && match(attr1,attr0)) {
                if(e == node) {
                  var index = option.noindex ? '' : '[' + j + ']';
                  xpath = '/' + nname + attr0.join('') + index + xpath;
                  break;
                }
                j++;
              }
            }
          }
        } else {
          if(option.attributes == 0) {
            for(var i=0, j=1; pnode.childNodes[i]; i++){
              var e = pnode.childNodes[i];
              if(e.nodeType == 1 && e.nodeName == node.nodeName) {
                if(e == node) {
                  var index = option.noindex ? '' : '[' + j + ']';
                  xpath = '/' + nname + index + xpath;
                  break;
                }
                j++;
              }
            }

          } else if(node.id) {
            //idが設定されているときはこれを条件として設定する
            var id = node.getAttribute('id');
            for(var i=0, j=1; pnode.childNodes[i]; i++){
              var e = pnode.childNodes[i];
              if(e.nodeType == 1 && e.nodeName == node.nodeName && e.id == id) {
                if(e == node) {
                  var index = option.noindex ? '' : '[' + j + ']';
                  xpath = '/' + nname + '[@id=' + tostring(id) + ']' + index + xpath;
                  break;
                }
                j++;
              }
            }
          } else if(option.attributes == 1 || option.attributes == undefined) {
            //classを条件として設定する
            var class0 = getattr(node.getAttributeNode('class'));
            for(var i=0, j=1; pnode.childNodes[i]; i++) {
              var e = pnode.childNodes[i];
              var class1 = getattr(e.nodeType==1 && e.getAttributeNode('class'));
              if(e.nodeType == 1 && e.nodeName == node.nodeName && match(class1,class0)) {
                if(e == node) {
                  var index = option.noindex ? '' : '[' + j + ']';
                  xpath = '/' + nname + class0.join('') + index + xpath;
                  break;
                }
                j++;
              }
            }
          } else if(option.attributes == 2) {
            //class, styleを条件として設定する
            var class0 = getattr(node.getAttributeNode('class'));
            var style0 = getattr(node.getAttributeNode('style'));
            for(var i=0, j=1; pnode.childNodes[i]; i++) {
              var e = pnode.childNodes[i];
              var class1 = getattr(e.nodeType==1 && e.getAttributeNode('class'));
              var style1 = getattr(e.nodeType==1 && e.getAttributeNode('style'));
              if(e.nodeType == 1 && e.nodeName == node.nodeName && match(class1,class0) && match(style1,style0)) {
                if(e == node) {
                  var index = option.noindex ? '' : '[' + j + ']';
                  xpath = '/' + nname + style0.join('') + class0.join('') + index + xpath;
                  break;
                }
                j++;
              }
            }
          }
        }
      }
      node = pnode;
    }
    //オプション設定
    if(option.equals) {
      xpath += '[.=' + tostring(option.equals) + ']';
    } else if(option.contains) {
      xpath += '[contains(.,' + tostring(option.contains) + ')]';
    }
    return xpath;
  } catch(e) {
    //alert(e);
  }
  return ''
}

function getPartialXPath(elem, option) {
  try {
    var d = elem.ownerDocument;
    var contentType = d.contentType;
    var option = option||{};
    var content = elem.textContent.replace(/[\\r\\n\\s]/g, '');
    var extractnodes = function(elem, xpath) {
      var d = elem.nodeType==9 ? elem : elem.ownerDocument;
      var iterator = d.evaluate(xpath, elem, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
      for(var n=iterator.iterateNext(), result=[]; n; n=iterator.iterateNext()) {
        result.push(n);
      }
      return result;
    }
    var splitxpath = function(xpath) {
      var escapebrackets = function(str) {
        return str.replace(/\\[/g, '&#x5B;').replace(/\\]/g, '&#x5D;');
      }
      var unescapebrackets = function(str) {
        return str.replace(/&#x5B;/g, '[').replace(/&#x5D;/g, ']');
      }
      var xpath1 = xpath.replace(/('[\\[\\]]'|"[\\[\\]]")/g, escapebrackets)
      var a = xpath1.match(/(?:\\/{2}|[a-z0-9:\\.\\-\\(\\)\\@\\*]+(?:\\[.*?\\])*)/g);
      var r = [];
      if(a) {
        for(var i=0; i<a.length; i++) {
          if(a[i] == '//') {
            r[i] = '';
          } else {
            r[i] = a[i].replace(/('(?:&#x5B;|&#x5D;)'|"(?:&#x5B;|&#x5D;)")/g, unescapebrackets);
          }
        }
      }
      return r;
    }
    var check = function(xpath) {
      var nodes = extractnodes(document, xpath);
      if(nodes.length == 1) {
        if(option.nocrop) {
          return nodes[0] && nodes[0] === elem;
        } else if(content) {
          return nodes[0] && nodes[0].textContent && nodes[0].textContent.replace(/[\\r\\n\\s]/g, '') == content;
        } else {
          return nodes[0] && nodes[0] === elem;
        }
      }
      return false;
    }
    var xpath = getFullXPath(elem, option);
    var a = splitxpath(xpath);
    var b = [];
    var c = [];
    for(var i=1; i<=a.length; i++) {
      //[1,2,3,4,5] -> [5],[4,5],[3,4,5],[2,3,4,5],...
      b = a.slice(-i);
      var xpath2 = '//' + b.join('/');
      if(check(xpath2)) {
        for(var j=1; j<=b.length; j++) {
          //[2,3,4,5] -> [2],[2,3],[2,3,4],...
          c = b.slice(0, j);
          var xpath2 = '//' + c.join('/');
          if(check(xpath2)) {
            return xpath2 ;
            break;
          }
        }
        break;
      }
    }
    return xpath;
  } catch(e) {
    //alert(e);
  }
  return '';
}

return getPartialXPath(arguments[0], arguments[1]);
"""

extractNodes = """
function extractNodes(xpath) {
  var iterator = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
  for(var n=iterator.iterateNext(), result=[]; n; n=iterator.iterateNext()) {
    result.push(n);
  }
  return result;
}

return extractNodes(arguments[0])
"""

# テスト用
if __name__  == '__main__':
    from selenium import webdriver
    from datetime import datetime
    driver = webdriver.Chrome()
    driver.get('http://www.goo.ne.jp/')
    elems = driver.find_elements_by_xpath('//div')
    #print driver.execute_script(getPartialXPath, elem)
    elems = driver.execute_script(extractNodes, '//div')
    driver.quit()
