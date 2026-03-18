import cups

conn = cups.Connection()

printers = conn.getPrinters()
printer_name = list(printers.keys())[0]
for name in printers:
    print(name)

ppd_path = conn.getPPD(conn.getDefault())
ppd = cups.PPD(ppd_path)

for group in ppd.optionGroups:
    for opt in group.options:
        if "color" in opt.keyword.lower():
            print(opt.keyword, [c["choice"] for c in opt.choices])

options = {"copies" : "1", 
            "sides": "two-sided-long-edge",
            "ColorModel": "Gray"
        }

job_id = conn.printFile(printer_name, "Hello world.pdf", "My Printing", options)
print(f"Job submitted: {job_id}")