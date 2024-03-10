
def quote(value: str, prefix="") -> str:
    # used to add quotation to input with a chosen prefix
    # (ex:   ex -> "ex")
    if value[0] != '"':
        value = f'"{prefix + value}"'
        pass
    else:
        value = '"' + prefix + value[1:]
    return value


def jsonFormat(tagName: str, value: str) -> str:
    # result should be "tagName": "value"
    tagName = quote(tagName)
    value = quote(value)
    return f'{tagName}: {value}'


def outputAppend(output: str, indentionLevel: int, data) -> str:
    # this function only add indention and data to the output
    # just to make the code more clean
    output += indentionLevel * INDENTION + data
    return output


def getTagName(header: str) -> str:
    # this function gets first encountered tag name in the input
    startIndex = header.find("<")
    endIndex = header.find(" ", startIndex)
    if (endIndex == -1) or endIndex > header.find(">"):
        endIndex = header.find(">")
        pass
    return header[startIndex + 1:endIndex]


def getValue(data: str, tagName: str) -> str:
    # this function gets the value of a tag given its name
    # the value is held in between > and <
    # ex <tagName attributes>VALUE</tagName>
    openStartIndex = data.find(f"<{tagName}")
    openEndIndex = data.find(">", openStartIndex)
    closeStartIndex = data.find(f"</{tagName}", openEndIndex)

    return data[openEndIndex + 1:closeStartIndex]


def getTagHeader(data: str, tagName: str) -> str:
    # this function used to get the opening tag header
    # ex    <element attributes>Value</element>
    #     will result <element attribute>
    openStartIndex = data.find(f"<{tagName}")
    openEndIndex = data.find(">", openStartIndex)

    return data[openStartIndex:openEndIndex + 1]


def xmlGetTagAttributes(data: str, tagName: str) -> list:
    # this function used to extract attributes from tag header given tag name

    header = getTagHeader(data, tagName)
    startIndex = header.find(" ")
    endIndex = header.find("/>")
    if endIndex == -1:
        endIndex = header.find(">")
    if startIndex == -1 or endIndex == -1:
        return []
    return [[x.split("=")[0], x.split("=")[1]] for x in header[startIndex + 1:endIndex].split(" ")]


def getXMLElement(data: str, tagName: str):
    # this function extract the complete xml element given its tag name
    # ex        <a1><a2>value</a2></a1>   given tag name = a2
    #       the result will be      <a2>value</a2>
    start = data.find(f"<{tagName}")
    # assume it's a self-closing tag
    selfClosingEnd = data.find("/>")
    end = data.find(f"</{tagName}>")

    if selfClosingEnd == -1 and end == -1:
        print("Error in tag: " + tagName)
        pass

    if (selfClosingEnd < end and selfClosingEnd != -1) or end == -1:
        end = selfClosingEnd + 2
        pass
    # elif end < selfClosingEnd and end != -1:
    else:
        end += len(f"</{tagName}>")

    return data[start:end]


def doesElementHaveSubElements(data: str) -> bool:
    # find if the closing of the tag is in the same position of next (<)
    # Note this will make self-closing tags always considered as have elements (it's useful)
    tagName = getTagName(data)
    startIndex = data.find(">")
    if data.find("<", startIndex) == data.find(f"</{tagName}"):
        return False
    return True


def xmlIsSelfClosing(data: str, tagName: str) -> bool:
    # check if the last two chars in the header are (/>)
    header = getTagHeader(data, tagName)
    if header[-2:] == "/>":
        return True
    return False


def xmlExtractSubElements(xmlElementsData: str):
    # the input of the function should be the inner value of xml element    (ex: <element>innerValue</element>)
    tags = []
    xmlElements = []

    # remainingXML represent the left XML to be processed
    remainingXML = xmlElementsData

    # check if there is sub elements left
    while not (remainingXML.isspace() or len(remainingXML) == 0):

        # get Next first Tag Name
        currentTagName = getTagName(remainingXML)

        # get the value it holds
        currentXMLElement = getXMLElement(remainingXML, currentTagName)

        # if the element tag found in the tags then it's a repeated xml
        # then convert its value to array and append the old one
        if currentTagName in tags:
            old = xmlElements[tags.index(currentTagName)]
            if type(old) is str:
                xmlElements[tags.index(currentTagName)] = []
                xmlElements[tags.index(currentTagName)].append(old)
                pass

            xmlElements[tags.index(currentTagName)].append(currentXMLElement)

        else:
            tags.append(currentTagName)
            xmlElements.append(currentXMLElement)
            pass

        # find the index of the end of the current element
        #                                   | (this is the end index )
        #                                   Y
        #      <element>innerValue</element>
        # or   <element attributes=1111111/>

        selfClosingEndIndex = remainingXML.find("/>")
        index = remainingXML.find(f"</{currentTagName}>")
        if selfClosingEndIndex == -1 and index == -1:
            print("Error in tag: " + currentTagName)

        if (selfClosingEndIndex < index and selfClosingEndIndex != -1) or index == -1:
            index = selfClosingEndIndex + 2
            pass
        else:
            index += len(f"</{currentTagName}>")
            pass

        # update the remaining xml by removing the processed one
        remainingXML = remainingXML[index:]
        pass
    return tags, xmlElements
    pass


def convertToNormalTag(data: str, tagName: str) -> str:
    # convert self-closing tag to normal one by removing replacing (/>) with (></tagName>)
    return data[:-2] + f"></{tagName}>"


def insertTagOpening(indentionLevel, insertTagName, output, tagName):
    # if we are processing repeated xml we should add the tag name since it's already added in caller function
    if insertTagName:
        output = outputAppend(output, indentionLevel, quote(tagName) + ': {\n')
    else:
        output = outputAppend(output, indentionLevel, "{\n")
    return output


def processSubElements(indentionLevel, output, subElements, tags):
    # the input is the childes of a tag
    # this function process child by child and return its json format
    for element in subElements:

        if type(element) is list:  # it's a repeated xml
            # insert repeated xml tag name with [ so it will be      "tagName": [
            tag = tags[subElements.index(element)]
            output = outputAppend(output, indentionLevel, quote(tag) + ': [\n')

            # get json of inner xml repeated elements with printing its tag name
            # because it was already printed in the previous line
            for item in element:
                output += recurseXMLtoJSON(item, indentionLevel + 1, False) + ",\n"
                pass
            # fix last element excess (,)
            output = output[:-2] + "\n"
            # close the repeated xml with ]
            output = outputAppend(output, indentionLevel, "],\n")
            pass

        elif type(element) is str:  # it's not repeated xml element so get format of json element
            output += recurseXMLtoJSON(element, indentionLevel) + ",\n"
            # fix last element excess (,)
            if subElements.index(element) == len(subElements) - 1 and output[-3] == ',':
                output = output[:-3] + "\n"
            else:
                output = output[:-2] + "\n"

        pass
    return output


def processTagTextValue(indentionLevel, isSelfClosing, output, tagName, xmlData):
    # processing text Values if the tag wasn't self-closing one (because it doesn't hold text)
    if not isSelfClosing:
        text = getValue(xmlData, tagName)
        if not (text.isspace() or len(text) == 0):
            output = outputAppend(output, indentionLevel + 1,
                                  jsonFormat(tagTextValuePrefix + "text", text) + ',\n')  # "#text": "value",

    return output


def processTagAttributes(attributes, indentionLevel, output, tagName):
    # this tag process the tag attributes and return it in json format
    output = outputAppend(output, indentionLevel, quote(tagName) + ': ' + "{\n")  # "tag": {
    # looping through each attribute and value
    for attr, value in attributes:
        output = outputAppend(output, indentionLevel + 1,
                              jsonFormat(quote(attr, tagAttributesPrefix), value) + ',\n')  # "@attr": "value",
    return output


def recurseXMLtoJSON(xmlData: str, indentionLevel: int, insertTagName: bool = True):
    # the main function in processing the xml data and converting it to json format
    tagName = getTagName(xmlData)
    output = ""

    if doesElementHaveSubElements(xmlData):

        # extract sub elements (not attributes)
        tags, subElements = xmlExtractSubElements(getValue(xmlData, tagName))

        # choose to insert tag name as ("element": {) or only insert ({)
        # this choice based on is this is a repeated xml or not since we deal with it as an array in json
        # (ex: "array": [ {"el":"val"},{"el":"val"}]
        output = insertTagOpening(indentionLevel, insertTagName, output, tagName)

        # process sub elements
        output = processSubElements(indentionLevel + 1, output, subElements, tags)

        # close opened tag (}) since the program finished processing its sub elements
        output = outputAppend(output, indentionLevel, "}")

        pass

    else:
        # check for self-closing tag then convert it to normal one
        isSelfClosing = xmlIsSelfClosing(xmlData, tagName)
        if isSelfClosing:
            xmlData = convertToNormalTag(xmlData, tagName)
            pass

        # checking if there is attributes
        attributes = xmlGetTagAttributes(xmlData, tagName)
        if len(attributes) != 0:

            # process attributes
            # element in form of  <tag attr=value>text</tag>
            output = processTagAttributes(attributes, indentionLevel, output, tagName)

            # process tag Text value        (ex: <element>TextValue</element>)
            output = processTagTextValue(indentionLevel, isSelfClosing, output, tagName, xmlData)

            # removing last element (,) because it's not needed (every added element add (,) with it)
            output = output[:-2] + "\n"

            # close tag
            output = outputAppend(output, indentionLevel, "},")  # }
        else:

            # it has no attributes so it's simplest form  (ex: <element>value</element>)
            output = outputAppend(output, indentionLevel, jsonFormat(tagName, getValue(xmlData, tagName)))

    return output


def xmlToJSON(xmlData: str) -> str:
    # function to prepare the data input to json recursive function

    # removing comments
    xmlData = cleanData("<!--", "-->", xmlData)

    # removing xml declarations
    xmlData = cleanData("<?", "?>", xmlData)

    output = recurseXMLtoJSON(xmlData, 1)

    # replacing some differences between xml and json
    output = output.replace('"True"', 'true')

    return "{\n" + output + "\n}"


def cleanData(start, end, xmlData):
    # function used to remove un wanted tags based on its opening tag and closing one
    # ex: removing xml comments based on        <!-- and -->

    startIndex = xmlData.find(start)
    endIndex = xmlData.find(end, startIndex)
    while True:

        if startIndex == -1 or endIndex == -1:
            break
            pass
        # removing unwanted part
        xmlData = xmlData[:startIndex] + xmlData[endIndex + len(end):]
        startIndex = xmlData.find(start, startIndex)
        endIndex = xmlData.find(end, startIndex)
    return xmlData


xmlSample = """
<?xml version="1.0" encoding="UTF-8"?>
<!-- This is a comment -->
<bookstore owner="owner">
  <book category="cooking">
    <title lang="en">Everyday Italian</title>
    <price>30.00</price>
  </book>
  <book>
    <title lang="en">Harry Potter</title>
    <price>29.99</price>
  </book>
  <selfClosing attr1="1" attr2="5" attr3="true"/>
</bookstore>
"""

INDENTION = "  "
tagAttributesPrefix = "@"
tagTextValuePrefix = "#"

print(xmlToJSON(xmlSample))
