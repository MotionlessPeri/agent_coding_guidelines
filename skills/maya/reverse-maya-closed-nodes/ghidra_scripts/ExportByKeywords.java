// 按关键词批量定位并反编译目标函数(泛化自 maya_reverse 的 ExportPWrapTargets)。
// 仅读取当前已分析的 Ghidra Program;换关键词即可复用到任何带符号 native DLL。
// 用法: analyzeHeadless <proj> <name> -process <dll> -noanalysis
//         -scriptPath <dir> -postScript ExportByKeywords.java <outputDir> <kw1,kw2,...>

import java.io.File;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class ExportByKeywords extends GhidraScript {
    private String[] keywords;

    private boolean matches(String text) {
        if (text == null) return false;
        String lower = text.toLowerCase(Locale.ROOT);
        for (String keyword : keywords) {
            if (!keyword.isEmpty() && lower.contains(keyword)) return true;
        }
        return false;
    }

    private void addFunction(Map<Address, Function> targets, Function function) {
        if (function != null) targets.put(function.getEntryPoint(), function);
    }

    private String fullName(Function function) {
        Symbol symbol = function.getSymbol();
        return symbol == null ? function.getName() : symbol.getName(true);
    }

    private String safeName(String name) {
        String safe = name.replaceAll("[^A-Za-z0-9._-]+", "_");
        if (safe.length() > 120) safe = safe.substring(0, 120);
        return safe;
    }

    private List<Function> sortedFunctions(Collection<Function> functions) {
        List<Function> result = new ArrayList<>(functions);
        result.sort(Comparator.comparing(Function::getEntryPoint));
        return result;
    }

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) {
            throw new IllegalArgumentException("Expected <outputDir> <comma-separated-keywords>");
        }
        File outputDir = new File(args[0]);
        keywords = args[1].toLowerCase(Locale.ROOT).split("\\s*,\\s*");

        File decompiledDir = new File(outputDir, "decompiled");
        if (!decompiledDir.exists() && !decompiledDir.mkdirs()) {
            throw new IllegalStateException("Cannot create " + decompiledDir);
        }

        Map<Address, Function> targets = new LinkedHashMap<>();
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext()) {
            Function function = functions.next();
            if (matches(fullName(function)) || matches(function.getPrototypeString(false, false))) {
                addFunction(targets, function);
            }
        }

        SymbolIterator symbols = currentProgram.getSymbolTable().getAllSymbols(true);
        while (symbols.hasNext()) {
            Symbol symbol = symbols.next();
            if (!matches(symbol.getName(true))) continue;
            addFunction(targets, currentProgram.getFunctionManager().getFunctionContaining(symbol.getAddress()));
            ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(symbol.getAddress());
            while (refs.hasNext()) {
                Reference ref = refs.next();
                addFunction(targets,
                    currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress()));
            }
        }

        for (Data data : currentProgram.getListing().getDefinedData(true)) {
            Object value = data.getValue();
            String text = value instanceof String ? (String)value : null;
            if (!matches(text)) continue;
            ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(data.getAddress());
            while (refs.hasNext()) {
                Reference ref = refs.next();
                addFunction(targets,
                    currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress()));
            }
        }

        // 一层调用邻域也导出,便于从有名字入口滑进无符号内部函数。
        List<Function> seeds = sortedFunctions(targets.values());
        for (Function seed : seeds) {
            for (Function called : seed.getCalledFunctions(monitor)) addFunction(targets, called);
            for (Function caller : seed.getCallingFunctions(monitor)) addFunction(targets, caller);
        }

        DecompInterface decompiler = new DecompInterface();
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        if (!decompiler.openProgram(currentProgram)) {
            throw new IllegalStateException("Decompiler failed to open current program");
        }

        List<Function> ordered = sortedFunctions(targets.values());
        try (PrintWriter index = new PrintWriter(new File(outputDir, "target_index.txt"), "UTF-8")) {
            index.println("program=" + currentProgram.getName());
            index.println("imageBase=" + currentProgram.getImageBase());
            index.println("keywords=" + String.join(",", keywords));
            index.println("targetCount=" + ordered.size());
            index.println();

            int ordinal = 0;
            for (Function function : ordered) {
                monitor.checkCancelled();
                String name = fullName(function);
                String base = String.format("%03d_%s_%s", ordinal++, function.getEntryPoint(), safeName(name));
                File file = new File(decompiledDir, base + ".c");
                DecompileResults result = decompiler.decompileFunction(function, 120, monitor);

                index.println(function.getEntryPoint() + "\t" + name + "\t" + function.getPrototypeString(false, false));
                try (PrintWriter out = new PrintWriter(file, "UTF-8")) {
                    out.println("// address: " + function.getEntryPoint());
                    out.println("// name: " + name);
                    out.println("// prototype: " + function.getPrototypeString(false, false));
                    out.println("// decompileCompleted: " + result.decompileCompleted());
                    if (result.decompileCompleted() && result.getDecompiledFunction() != null) {
                        out.println();
                        out.println(result.getDecompiledFunction().getC());
                    } else {
                        out.println("// error: " + result.getErrorMessage());
                    }
                }
            }
        } finally {
            decompiler.dispose();
        }

        println("Exported " + ordered.size() + " functions to " + outputDir);
    }
}
