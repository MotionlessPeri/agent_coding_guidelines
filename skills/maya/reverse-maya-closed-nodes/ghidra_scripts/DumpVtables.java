// 导出匹配关键词的 MSVC vftable 每槽函数指针(泛化自 DumpPWrapVtables)。
// 用于恢复虚表/类结构。用法: ... -postScript DumpVtables.java <outputFile> <kw1,kw2,...>

import java.io.File;
import java.io.PrintWriter;
import java.util.Locale;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class DumpVtables extends GhidraScript {
    private String[] keywords;

    private boolean wanted(String name) {
        String lower = name.toLowerCase(Locale.ROOT);
        if (!lower.contains("vftable") || lower.contains("rtti_") || lower.contains("meta_ptr")) return false;
        for (String kw : keywords) {
            if (!kw.isEmpty() && lower.contains(kw)) return true;
        }
        return false;
    }

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) throw new IllegalArgumentException("Expected <outputFile> <comma-separated-keywords>");
        File output = new File(args[0]);
        keywords = args[1].toLowerCase(Locale.ROOT).split("\\s*,\\s*");
        if (output.getParentFile() != null) output.getParentFile().mkdirs();
        try (PrintWriter out = new PrintWriter(output, "UTF-8")) {
            SymbolIterator symbols = currentProgram.getSymbolTable().getAllSymbols(true);
            while (symbols.hasNext()) {
                Symbol symbol = symbols.next();
                if (!wanted(symbol.getName(true))) continue;
                Address cursor = symbol.getAddress();
                out.println("VTABLE\t" + cursor + "\t" + symbol.getName(true));
                int misses = 0;
                for (int slot = 0; slot < 160 && misses < 5; ++slot, cursor = cursor.add(8)) {
                    long raw;
                    try { raw = getLong(cursor); }
                    catch (Exception ex) { break; }
                    Address target = toAddr(raw);
                    Function function = currentProgram.getFunctionManager().getFunctionAt(target);
                    MemoryBlock block = currentProgram.getMemory().getBlock(target);
                    boolean executable = block != null && block.isExecute();
                    if (function == null && !executable) {
                        misses++;
                        out.println("  " + slot + "\t" + cursor + "\t" + target + "\t<non-code>");
                        continue;
                    }
                    misses = 0;
                    String name = function == null ? "<unnamed-code>" : function.getSymbol().getName(true);
                    out.println("  " + slot + "\t" + cursor + "\t" + target + "\t" + name);
                }
                out.println();
            }
        }
    }
}
