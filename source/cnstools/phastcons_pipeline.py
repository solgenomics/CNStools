import os
import json
from alignment_pipeline import call_commands_async

config_defaults = {
    #"per_genome_input_mafs": {"name":["chr_path","chr_path]},
    #"ref_genome_gff3": "path",
    #"reference": "Metru",
    #"tree": "",
    "out_folder":".",
    "multiz_bin_path": "",
    "msa_view_bin_path": "",
    "num_processes": 1,
}

def parser(parser_add_func,name):
    p = parser_add_func(name,description="Aligns a genome to a reference")
    p.add_argument("config_path", help="Absolute(!) path to config file")
    return p

def run(config_path):

    with open(config_path) as config_file:
      config = json.loads(config_file.read())
    for key in config_defaults:
        config.setdefault(key, config_defaults[key])

    per_genome_input_mafs = config["per_genome_input_mafs"]
    ref_genome_gff3 = config["ref_genome_gff3"]
    reference = config["reference"]
    tree = config["tree"]
    multiz_bin_path = config["multiz_bin_path"]
    msa_view_bin_path = config["msa_view_bin_path"]
    num_processes = config["num_processes"]
    out_folder = config["out_folder"]

    cmd_env = os.environ.copy()

    if multiz_bin_path!="":
            cmd_env["PATH"] = multiz_bin_path+":" + cmd_env["PATH"]

    per_chrom_labeled_mafs = {}
    out_name_template = os.path.join(out_folder,"{chrom}.{non_ref_genome}.sing.maf")
    for non_ref_genome in per_genome_input_mafs:
        for maf_name in per_genome_input_mafs[non_ref_genome]:
            out_name = os.path.join(out_folder,"temp.sing.maf")
            chrom, num_entries = prefix_and_get_chrom_and_count(maf_name,out_name,[reference,non_ref_genome])
            new_name = out_name_template.format(chrom=chrom,non_ref_genome=non_ref_genome)
            os.rename(out_name,new_name)
            if num_entries>0: #We dont need to do anything with the empty files!
                if chrom not in per_chrom_labeled_mafs: per_chrom_labeled_mafs[chrom] = []
                per_chrom_labeled_mafs[chrom].append(new_name)

    roast_commandlists = []
    for chrom in per_chrom_labeled_mafs:
        outfile = os.path.join(out_folder,chrom+".roast.maf")
        roast_commandlists.append(["roast",'E="%s"'%reference,"X=0", '"%s"'%tree, chrom+".*.sing.maf", outfile])
    roast_files = [l[-1] for l in roast_commandlists]
    call_commands_async(roast_commandlists,num_processes,shell=True,tracker_name="roast",env=cmd_env) #runs commands asynchronously with maximum simultanious process count

    prepared_for_msa = []
    for maf_name in roast_files:
        out_name = os.path.splitext(maf_name)[0]+".qchrom.maf"
        num_entries,chrom,non_ref_genome = remove_target_chrom_and_count(maf_name,out_name,reference)
        if num_entries > 0:
            prepared_for_msa.append(out_name)

    mas_commandlists = []
    for maf_name in prepared_for_msa:
        out_name = os.path.splitext(maf_name)+".4d-codons.ss"
        mas_commandlists.append(["msa_view","--in-format","MAF","--4d",maf_name,"--features",ref_genome_gff3,">",out_name])
    call_commands_async(mas_commandlists,num_processes,shell=True,tracker_name="msa",env=cmd_env)


def prefix_and_get_chrom_and_count(maf_name,out_maf,names):
    with open(maf_name) as maf, open(out_maf,"w") as out:
        a_count = 0
        s_count = -1
        for line in maf:
            if line.startswith("a"):
                s_count = 0
                a_count+= 1
            if line.startswith("s"):
                line_arr = line.split()
                if s_count==0: chrom = line_arr[1]
                else: line_arr[1] = "%s:%s" % (names[i],line_arr[1])
                line = " ".join(line_arr)+"\n"
                s_count+=1
            out.write(line)
    return chrom,a_count

def remove_target_chrom_and_count(maf_name,out_maf,ref_name):
    with open(maf_name) as maf, open(out_maf,"w") as out:
        a_count = 0
        for line in maf:
            if line.startswith("a"):
                s_count = 0
                a_count+= 1
            if line.startswith("s"):
                line_arr = line.split()
                if line_arr[1].startswith(ref_name): #if it is the reference, just use the chromosome name
                    line_arr[1] = line_arr[1].split(":",1)[1]
                else:                                #otherwise, use only the species identifier (ignore chromosome).
                    line_arr[1] = line_arr[1].split(":",1)[0]
                line = " ".join(line_arr)+"\n"
            out.write(line)
    return a_count