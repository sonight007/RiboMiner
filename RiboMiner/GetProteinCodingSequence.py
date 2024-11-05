#!/usr/bin/env python
# -*- coding:UTF-8 -*-
'''
In whole mode:
This script is used for getting transcript sequences, cds sequences and amino acid sequence  from protein coding genes.
In local mode:
This script is used for getting a local cds sequence with a specific region [left_pos to right_pos in codon unit]
input:
1) transcripts_sequences.fa: all transcript sequences generated by RiboCode.
2) longest.trans.info.txt: coordinate of the longest cds sequences for protein coding genes generated by OutputTranscriptInfo.py.

output:
1) longest_transcripts_cds.fa: transcript sequences of protein genes in DNA level.
3) longest_transcripts_cds_ORFs.fa: cds sequences of protein coding genes in DNA level.
5) longest_transcripts_aa.fa: amino acid sequences of protein coding genes. Translated from transcripts_cds_DNA.fa.
'''

from .FunctionDefinition import *


def extract_protein_coding_sequence(transcriptFile,startCodonCoorDict,stopCodonCoorDict,in_selectTrans,output_prefix,table):
	'''
	This function is used for extacting sequences of protein coding genes based on transcript_sequences.fa generated by RiboCode.
	'''
	trans_sequence_dict=fastaIter(transcriptFile)
	in_selectTrans=in_selectTrans.intersection(trans_sequence_dict.keys()).intersection(startCodonCoorDict.keys())
	i=0
	with open(output_prefix+"_transcript_sequences.fa",'w') as f1,open(output_prefix+"_cds_sequences.fa",'w') as f2,open(output_prefix+"_amino_acid_sequences.fa",'w') as f3:
		for trans in in_selectTrans:
			trans_sequence=trans_sequence_dict[trans]
			startCoor=int(startCodonCoorDict[trans])-1 # 0-based
			stopCoor=int(stopCodonCoorDict[trans])-3 # 0-based , the first base of stop codon
			cds_sequence=trans_sequence[startCoor-21:(stopCoor+24)]
			AA_sequence=translation(cds_sequence,table=table,cds=False)
			AA_sequence_length=len(AA_sequence)
			trans_sequence_length=len(trans_sequence)
			cds_sequence_length=len(cds_sequence)
			if cds_sequence_length%3 !=0:
				i+=1
			f1.write("%s%s\n" %(">",str(trans)+" "+str(trans_sequence_length)))
			f1.write("%s\n" %(trans_sequence))
			f2.write("%s%s\n" %(">",str(trans)+" "+str(cds_sequence_length)))
			f2.write("%s\n" %(cds_sequence))
			f3.write("%s%s\n" %(">",str(trans)+" "+str(AA_sequence_length)))
			f3.write("%s\n" %(AA_sequence))
	print("Notes: There are " + str(i) +" transcripts whose cds sequence cannot be divided by 3!",file=sys.stderr)
def extract_local_cds_sequence(transcriptFile,startCodonCoorDict,stopCodonCoorDict,in_selectTrans,output_prefix,left_pos,right_pos,table):
	'''
	This script is used for extracting a local sequence of a given cds sequence. And you have to offer a left position and right position you wanna to extract.
	And the position is in codon unit.
	'''
	trans_sequence_dict=fastaIter(transcriptFile)
	in_selectTrans=in_selectTrans.intersection(trans_sequence_dict.keys()).intersection(startCodonCoorDict.keys())
	with open(output_prefix+"_local_cds_sequences_RNA.fa",'w') as f1, open(output_prefix+"_local_cds_sequence_DNA.fa",'w') as f2, open(output_prefix+"_local_AA_sequences.fa",'w') as f3:
		for trans in in_selectTrans:
			trans_sequence=trans_sequence_dict[trans]
			startCoor=int(startCodonCoorDict[trans])-1 # 0-based
			stopCoor=int(stopCodonCoorDict[trans])-3 # 0-based , the first base of stop codon
			cds_sequence=trans_sequence[startCoor:(stopCoor+3)]
			AA_sequence=translation(cds_sequence,table=table,cds=False)
			local_cds_sequence=cds_sequence[3*(int(left_pos)-1):3*int(right_pos)]
			local_cds_sequence_RNA=local_cds_sequence.replace("T","U")
			local_AA_sequence=AA_sequence[(int(left_pos)-1):int(right_pos)]
			if len(local_AA_sequence) < (int(right_pos)-int(left_pos)+1):
				continue
			if len(local_cds_sequence_RNA) < (int(right_pos)-int(left_pos))*3+1:
				continue
			if len(local_cds_sequence) < (int(right_pos)-int(left_pos))*3+1:
				continue
			f1.write("%s%s\n%s\n" %(">",trans,local_cds_sequence_RNA))
			f2.write("%s%s\n%s\n" %(">",trans,local_cds_sequence))
			f3.write("%s%s\n%s\n" %(">",trans,local_AA_sequence))


def main():
	parser=create_parser_for_sequence_extraction()
	(options,args)=parser.parse_args()
	if not options.transcriptFile:
		raise IOError("Please enter the fasta file of all transcript sequences. Generated by RiboCode if in whole mode, or a given cds sequences in local mode.")
	if not options.coorFile:
		raise IOError("Please enter the longest.trans.info.txt file generated by OutputTranscriptInfo.py")
	selectTrans,transLengthDict,startCodonCoorDict,stopCodonCoorDict,transID2geneID,transID2geneName,cdsLengthDict,transID2ChromDict=reload_transcripts_information(options.coorFile)
	geneID2transID={v:k for k,v in transID2geneID.items()}
	geneName2transID={v:k for k,v in transID2geneName.items()}
	if options.in_selectTrans:
		select_trans=pd.read_csv(options.in_selectTrans,sep="\t")
		select_trans=set(select_trans.iloc[:,0].values)
		if options.id_type == 'transcript_id':
			select_trans=select_trans.intersection(selectTrans)
			print("There are " + str(len(select_trans)) + " transcripts from "+options.in_selectTrans+" used for following analysis.",file=sys.stderr)
		elif options.id_type == 'gene_id':
			tmp=[geneID2transID[gene_id] for gene_id in select_trans if gene_id in geneID2transID]
			select_trans=set(tmp)
			select_trans=select_trans.intersection(selectTrans)
			print("There are " + str(len(select_trans))+" gene id could be transformed into transcript id and used for following analysis.",file=sys.stderr)
		elif options.id_type == 'gene_name' or options.id_type=='gene_symbol':
			tmp=[geneName2transID[gene_name] for gene_name in select_trans if gene_name in geneName2transID]
			select_trans=set(tmp)
			select_trans=select_trans.intersection(selectTrans)
			print("There are " + str(len(select_trans))+" gene symbol could be transformed into transcript id and used for following analysis.",file=sys.stderr)
		else:
			raise IOError("Please input a approproate id_type parameters.[transcript_id/gene_id/gene_name/]")
	else:
		select_trans=selectTrans
	if options.mode == "whole":
		extract_protein_coding_sequence(options.transcriptFile,startCodonCoorDict,stopCodonCoorDict,select_trans,options.output_prefix,options.geneticCode)
		print("Finish the step of extracting sequences!",file=sys.stderr)
	elif options.mode == "local":
		extract_local_cds_sequence(options.transcriptFile,startCodonCoorDict,stopCodonCoorDict,select_trans,options.output_prefix,options.left_position,options.right_position,options.geneticCode)
		print("Finish the step of extracting sequences!",file=sys.stderr)
	else:
		raise IOError("Please enter a correct --mode parameter! [whole/local]")


if __name__=="__main__":
	main()

