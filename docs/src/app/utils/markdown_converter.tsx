import { Converter } from "showdown";
import parse from "html-react-parser"

function md_converter(text:string) {
    const converter = new Converter();
    return parse(converter.makeHtml(text));
}

export default md_converter