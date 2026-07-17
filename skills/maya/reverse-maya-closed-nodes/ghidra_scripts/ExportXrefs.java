// 导出匹配关键词的字符串/符号的引用点及所在函数(泛化自 ExportPWrapRefs)。
// 辅助定位无导出符号的内部实现。用法: ... -postScript ExportXrefs.java <outputFile> <kw1,kw2,...>

import java.io.File;
import java.io.PrintWriter;
import java.util.Locale;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class ExportXrefs extends GhidraScript {
    private String[] keywords;

    private boolean matches(String text) {
        if (text == null) return false;
        String lower = text.toLowerCase(Locale.ROOT);
        for (String kw : keywords) if (!kw.isEmpty() && lower.contains(kw)) return true;
        return false;
    }

    private String functionName(Function function) {
        if (function == null) return "<no-function>";
        Symbol symbol = function.getSymbol();
        return symbol == null ? function.getName() : symbol.getName(true);
    }

    private void writeRefs(PrintWriter out, String kind, String value, Address address) {
        out.println(kind + "\t" + address + "\t" + value);
        ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(address);
        int count = 0;
        while (refs.hasNext()) {
            Reference ref = refs.next();
            Function function = currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());
            out.println("  REF\t" + ref.getFromAddress() + "\t" +
                (function == null ? "<no-entry>" : function.getEntryPoint().toString()) + "\t" +
                functionName(function));
            count++;
        }
        out.println("  REFCOUNT\t" + count);
        out.println();
    }

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) throw new IllegalArgumentException("Expected <outputFile> <comma-separated-keywords>");
        File output = new File(args[0]);
        keywords = args[1].toLowerCase(Locale.ROOT).split("\\s*,\\s*");
        File parent = output.getParentFile();
        if (parent != null) parent.mkdirs();

        try (PrintWriter out = new PrintWriter(output, "UTF-8")) {
            SymbolIterator symbols = currentProgram.getSymbolTable().getAllSymbols(true);
            while (symbols.hasNext()) {
                Symbol symbol = symbols.next();
                String name = symbol.getName(true);
                if (matches(name)) writeRefs(out, "SYMBOL", name, symbol.getAddress());
            }
            for (Data data : currentProgram.getListing().getDefinedData(true)) {
                Object value = data.getValue();
                if (!(value instanceof String)) continue;
                String text = (String)value;
                if (matches(text)) writeRefs(out, "STRING", text, data.getAddress());
            }
        }
    }
}
