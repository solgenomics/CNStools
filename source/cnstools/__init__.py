"""The cnstools package can be run in three ways. It can be run as an executable directly from the commandline, 
run as a python program with ``$python cnstools`` or it can be imported as a python module :class:`cnstools` and used with other 
python scripts. Currently this documentation only covers the imported module, more to come later."""

#A list of all task modules to be imported and added to __all__.
names = [
    "analyze_cns",
    "bed_maf_parse",
    "cns_to_fasta",
    "gff2_to_bed",
    "gff3_to_bed",
    "identify",
    "maf_to_bed",
    "maf_to_fasta",
    "parse_cns_data",
    "run_tomtom_and_fimo"
]
__all__ = names
for name in names:
    exec "import %s"%(name)