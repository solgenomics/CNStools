from abc import ABCMeta, abstractmethod
from progress_tracker import Progress_tracker

class Filetype(object):
    """"""
    __metaclass__ = ABCMeta
    Entry_class = None
    def __init__(self,file_name=None,file_object=None,lines=None):
        self.entries = []
        if lines:
            self.add_lines(lines)
        elif file_object==None and file_name==None:
            return None
        else:
            with (file_object if file_object!=None else open(file_name)) as file:
                self.add_lines(file.readlines())

    def add_entry(self,*args,**kwargs): 
        if self.Entry_class:
            new_entry = self.Entry_class(*args,**kwargs) 
            self.entries.append(new_entry)
            return new_entry
        else: 
            return None

    @abstractmethod
    def add_lines(self,file): pass
    @abstractmethod
    def get_lines(self): pass

class Cns_sequence():
    def __init__(self,genome,type,dist,loc_chrom,closest_gene,start,stop,gene_start,gene_stop,sequence,cns_ID=None):
        self.cns_ID = cns_ID
        self.genome = genome
        self.type = type
        self.dist = int(dist) if dist else None
        self.loc_chrom = loc_chrom
        self.closest_gene = closest_gene
        self.start = int(start) if start else None
        self.stop = int(stop) if stop else None
        self.gene_start = int(gene_start) if gene_start else None
        self.gene_stop = int(gene_stop) if gene_stop else None
        self.sequence = sequence
    def get_line(self):
        strs = (str(i) if i!=None else '.' for i in (self.cns_ID,self.genome,self.type,self.dist,self.loc_chrom,self.closest_gene,self.start,self.stop,self.gene_start,self.gene_stop,self.sequence))
        return "\t".join(strs)
    def duplicate(self):
        return Cns_sequence(self.genome,self.type,self.dist,self.loc_chrom,self.closest_gene,self.start,self.stop,self.gene_start,self.gene_stop,self.sequence,cns_ID=self.cns_ID)

class Cns_entry():
    def __init__(self,cns_ID):
        self.cns_ID = cns_ID
        self.sequences = {}
    def add_seq(self,genome,*args):
        if not genome in self.sequences: self.sequences[genome] = []
        self.sequences[genome].append(Cns_sequence(genome,*args,cns_ID=self.cns_ID))
        return self.sequences[genome][-1]
    def get_seqs(self,genome=None):
        if genome==None: return [seq for key in self.sequences for seq in self.sequences[key]]
        elif not genome in self.sequences: return None
        else: return self.sequences[genome][:]
    def get_lines(self):
        seqs = []
        for key in self.sequences:
            seqs+=self.sequences[key]
        return [seq.get_line() for seq in seqs]


class Cns(Filetype):
    Entry_class = Cns_entry
    def add_lines(self,lines):
        ID=None
        tracker = Progress_tracker("Parsing .cns",len(lines)).display(estimate=False,rate=0.5)
        for line in lines:
            list = [item if item!='.' else None for item in line.split('\t')]
            if list[0]!=ID:
                ID = list[0]
                self.entries.append(Cns_entry(ID))
            self.entries[-1].add_seq(*(list[1:]))
            tracker.step()
        tracker.display()
        del tracker

    def get_lines(self):
        return [line for entry in self.entries for line in entry.get_lines()]
    def to_fasta(self,sequences=False):
        fastas = {}
        tracker = Progress_tracker("Converting to .fasta files",len(self.entries)).display(estimate=False,rate=0.5)
        for entry in self.entries:
            for seq in [seq for key in entry.sequences for seq in entry.sequences[key]]:
                if seq.genome not in fastas: fastas[seq.genome] = Fasta()
                description = "|".join((str(a) for a in (seq.cns_ID,seq.type,seq.loc_chrom,seq.start,seq.stop)))
                fastas[seq.genome].add_entry(description,seq.sequence.replace("-", ""))
            tracker.step()
        tracker.display()
        del tracker
        return fastas



class Bed6_entry():
    """0-based"""
    def __init__(self, chrom, chromStart, chromEnd, name=None, score=None, strand=None):
        #super(Bed6_entry, self).__init__()
        self.chrom = chrom
        self.chromStart = int(chromStart)
        self.chromEnd = int(chromEnd)
        self.name = name
        try:
            self.score = float(score)
        except:
            self.score = None
        self.strand = strand
    def get_line(self):
        strs = (str(i) if i!=None else '.' for i in (self.chrom, self.chromStart, self.chromEnd, self.name, self.score, self.strand))
        return "\t".join(strs)

class Bed6(Filetype):
    """0-based"""
    Entry_class = Bed6_entry
    def add_lines(self,lines):
        tracker = Progress_tracker("Parsing 6 column .bed",len(lines)).display(estimate=False,rate=0.5)
        for line in lines:
            fields = line.strip().split('\t')
            if len(fields>1):
                if len(fields)<6:
                    fields.append([None]*(6-len(fields)))
                fields[:] = [item if item!='.' else None for item in fields]
                self.entries.append(Bed6_entry(*fields))
            tracker.step()
        tracker.display()
        del tracker
    def get_lines(self):
        lines = []
        for entry in self.entries:
            lines.append(entry.get_line())
        return lines

class Bed13_entry():
    def __init__(self,*fields):
        if len(fields)!=13:
            raise Exception("not 13 fields")
        self.first = Bed6_entry(*(fields[0:6]))
        self.second = Bed6_entry(*(fields[6:12]))
        self.score = int(fields[12])
    def get_line(self):
        return "\t".join([self.first.get_line(),self.second.get_line(),str(self.score)])

class Bed13(Filetype):
    """0-based"""
    Entry_class = Bed13_entry
    def add_lines(self,lines):
        for line in lines:
            fields = line.strip().split('\t')
            if len(fields)>1:
                if len(fields)<13:
                    fields.append([None]*(13-len(fields)))
                fields[:] = [item if item!='.' else None for item in fields]
                self.entries.append(Bed13_entry(*fields))
    def get_lines(self):
        lines = []
        for entry in self.entries:
            lines.append(entry.get_line())
        return lines
        
class BlastF6_entry(object):
    """1-based"""
    def __init__(self,query,target,identity,length,mismatches,gapOpens,queryStart,queryEnd,targetStart,targetEnd,eVal,bitScore):
        #super(BlastF6_entry, self).__init__()
        self.query = query
        self.target = target
        self.identity = float(identity)
        self.length = int(length)
        self.mismatches = int(mismatches)
        self.gapOpens = int(gapOpens)
        self.queryStart = int(queryStart)
        self.queryEnd = int(queryEnd)
        self.targetStart = int(targetStart)
        self.targetEnd = int(targetEnd)
        self.eVal = float(eVal)
        self.bitScore = float(bitScore)
    def get_line(self):
        return "\t".join([str(item) for item in (self.query,self.target,self.identity,self.length,self.mismatches,self.gapOpens,self.queryStart,self.queryEnd,self.targetStart,self.targetEnd,self.eVal,self.bitScore)])

class BlastF6(Filetype):
    """1-based"""
    Entry_class = BlastF6_entry
    def add_lines(self,lines):
        tracker = Progress_tracker("Parsing blast output",len(lines)).display(estimate=False,rate=0.5)
        for line in lines:
            fields = line.strip().split('\t')
            if (len(fields)==12):
                self.entries.append(BlastF6_entry(*fields))
            tracker.step()
        tracker.display()
        del tracker
    def get_lines(self):
        lines = []
        for entry in self.entries:
            lines.append(entry.get_line())
        return lines
    def to_bed(self):
        new_bed = Bed6()
        tracker = Progress_tracker("Converting to .bed",len(self.entries)).display(estimate=False,rate=0.5)
        for entry in self.entries:
            strand = None
            if entry.targetStart < entry.targetEnd:
                start, end = entry.targetStart, entry.targetEnd
                strand = '+'
            else:
                start, end = entry.targetEnd, entry.targetStart
                strand = '-'
            #convert to 0-based!
            new_bed.add_entry(entry.target, start-1, end, entry.query, entry.bitScore, strand)
            tracker.step()
        tracker.display()
        del tracker
        return new_bed

class Gff3_entry(object):
    """1-based"""
    def __init__(self,seqid,source,type,start,end,score,strand,phase,attributes):
        #super(Gff3_entry, self).__init__()
        self.seqid = seqid
        self.source = source
        self.type = type
        self.start = int(start)
        self.end = int(end)
        try:
            self.score = float(score)
        except:
            self.score = None
        self.strand = strand
        self.phase = phase
        self.attributes = attributes
    def get_line(self):
        return "\t".join([str(item) for item in (self.seqid,self.source,self.type,self.start,self.end,self.score,self.strand,self.phase,self.attributes)])

class Gff3(Filetype):
    """1-based"""
    Entry_class = Gff3_entry
    def add_lines(self,lines):
        tracker = Progress_tracker("Parsing .gff3",len(lines)).display(estimate=False,rate=0.5)
        for line in lines:
            fields = line.strip().split('\t')
            if (len(fields)==9):
                self.entries.append(Gff3_entry(*fields))
            tracker.step()
        tracker.display()
        del tracker
    def get_lines(self):
        lines = []
        for entry in self.entries:
            lines.append(entry.get_line())
        return lines
    def to_bed(self,type_list=None):
        new_bed = Bed6()
        entry_selection = None
        if(type_list):
            entry_selection = [entry for entry in self.entries if entry.type in type_list]
        else:
            entry_selection = self.entries
        tracker = Progress_tracker("Converting to .bed",len(entry_selection)).display(estimate=False,rate=0.5)
        for entry in entry_selection:
            if(entry.start<entry.end):
                chromStart,chromEnd = entry.start,entry.end
            else:
                chromStart,chromEnd = entry.end,entry.start
            id_with_type = entry.attributes+";seqType="+entry.type
            new_bed.add_entry(entry.seqid, chromStart-1, chromEnd, name=id_with_type, score=entry.score, strand=entry.strand)
            tracker.step()
        tracker.display()
        del tracker
        return new_bed

class Maf_sequence(object):
    def __init__(self,src,start,size,strand,srcSize,text,metadata=None):
        self.src = src
        self.start = int(start)
        self.size = int(size)
        self.strand = strand
        self.srcSize = int(srcSize)
        self.text = text
        self.metadata = metadata
    def get_lines(self):
        lines = ['##'+metadata] if metadata else []
        lines.append('\t'.join([str(item) for item in [self.src,self.start,self.size,self.strand,self.srcSize,self.text]]))
        return lines
        
class Maf_entry(object):
    def __init__(self,paragraph=None):
        self.a_meta = None
        self.a_line = None
        self.sequences = []
        if paragraph:
            rec_metadata = None
            for line in paragraph:
                if line.startswith('##'):
                    rec_metadata = line.split("##")[1]
                elif line.startswith('a'):
                    self.a_line = line
                    if rec_metadata:
                        self.a_meta = rec_metadata
                        rec_metadata = None
                elif line.startswith('s'):
                    vals = line.split()[1:]
                    if rec_metadata:
                        vals.append(rec_metadata)
                        rec_metadata = None
                    self.sequences.append(Maf_sequence(*vals))
    def get_lines(self):
        lines = []
        if self.a_meta: lines.append('##'+self.a_meta)
        if self.a_line: lines.append(self.a_line)
        for sequence in self.sequences:
            lines+=sequence.get_lines()
        return lines

class Maf(Filetype):
    """0-based"""
    Entry_class = Maf_entry
    def add_lines(self,lines):
        if not hasattr(self, 'headerLines'): self.headerLines = []
        paragraph = []
        tracker = Progress_tracker("Parsing .maf",len(lines)).display(estimate=False,rate=0.5)
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") and not stripped.startswith("##--"):
                self.headerLines.append(stripped)
            elif stripped=="":
                if len(paragraph)>1:
                    self.entries.append(Maf_entry(paragraph))
                paragraph = []
            else:
                paragraph.append(stripped)
            tracker.step()
        tracker.display()
        del tracker
    def get_lines(self):
        lines = []
        for entry in self.entries:
            lines+=entry.get_lines()
            lines.append("")
        return lines
    def to_bed(self,seq_name=None):
        new_bed = Bed6()
        tracker = Progress_tracker("Converting to .bed",len(self.entries)).display(estimate=False,rate=0.5)
        if not seq_name: 
            seq_name=self.entries[0].sequences[0].src
        for entry in self.entries:
            for sequence in (seq for seq in entry.sequences if seq.src==seq_name):
                new_bed.add_entry(sequence.src, sequence.start, sequence.start+sequence.size, name=sequence.metadata, strand=sequence.strand)
            tracker.step()
        tracker.display()
        del tracker
        return new_bed

class Fasta_entry(object):
    def __init__(self,description,sequence):
        self.description = description
        self.sequence = sequence
    def get_lines(self):
        return [">"+self.description]+[self.sequence[i:i+70] for i in range(0,len(self.sequence),70)]

class Fasta(Filetype):
    """docstring for Fasta"""
    Entry_class = Fasta_entry
    def add_lines(self,lines):
        paragraphs = [[]]
        first_found = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('>'):
                first_found = True
                paragraphs[-1].append([stripped[1:]])
            elif first_found:
                paragraphs[-1].append(stripped)
        for paragraph in paragraphs:
            self.entries.append(Fasta_entry(paragraph[0],"".join(paragraph[1:])))
    def get_lines(self):
        lines = []
        for entry in self.entries:
            lines+= entry.get_lines()
        return lines



        