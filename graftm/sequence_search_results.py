import subprocess
import logging
import csv

class SequenceSearchResult:
    QUERY_FROM_FIELD = 'query_from'
    QUERY_TO_FIELD = 'query_to'
    HIT_FROM_FIELD = 'hit_from'
    HIT_TO_FIELD = 'hit_to'
    ALIGNMENT_LENGTH_FIELD = 'alignment_length'
    ALIGNMENT_BIT_SCORE = 'alignment_bit_score'
    ALIGNMENT_DIRECTION = 'alignment_direction'
    HIT_ID_FIELD = 'hit_id'
    QUERY_ID_FIELD = 'query_id'
    
    def __init__(self):
        self.fields = []
        self.results = []
        
    def each(self, field_names):
        """Iterate over the results, yielding a list for each result, where
        each element corresponds to the field given in the field_name parameters
        
        Parameters
        ----------
        field_names: list of str
            The names of the fields to be returned during iteration
            
        Returns
        -------
        None
        
        Exceptions
        ----------
        raises something when a field name is not in self.fields
        """
        field_ids = []
        for f in field_names:
            # below raises error if the field name is not found, so
            # don't need to account for that.
            field_ids.append(self.fields.index(f))
        for r in self.results:
            yield([r[i] for i in field_ids])
        
class DiamondSearchResult(SequenceSearchResult):
    @staticmethod
    def import_from_daa_file(daa_filename):
        '''Generate new results object from the output of diamond blastx/p'''
        
        # blast m8 format is
        # 'qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore
        res = DiamondSearchResult()
        res.fields = [
                       SequenceSearchResult.QUERY_ID_FIELD,
                       SequenceSearchResult.HIT_ID_FIELD,
                       #skip
                       SequenceSearchResult.ALIGNMENT_LENGTH_FIELD,
                       #skip
                       #skip
                       SequenceSearchResult.QUERY_FROM_FIELD,
                       SequenceSearchResult.QUERY_TO_FIELD,
                       SequenceSearchResult.HIT_FROM_FIELD,
                       SequenceSearchResult.HIT_TO_FIELD,
                       #skip
                       SequenceSearchResult.ALIGNMENT_BIT_SCORE,
                       # extras
                       SequenceSearchResult.ALIGNMENT_DIRECTION,
                       ]
        
        cmd = "diamond view -a '%s'" % daa_filename
        logging.debug("Running cmd: %s" % cmd)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        
        reader = csv.reader(stdout.decode('ascii').splitlines(),
                                delimiter='\t')
        if process.returncode != 0:
            raise Exception("Problem running diamond view with cmd: '%s'," 
                            "stderr was %s" % (cmd, stderr))

        for row in reader:
            # 'qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore
            #    0       1     2      3        4        5      6     7    8      9    10     11
            query_start = int(row[6])
            query_end = int(row[7])
            res.results.append([row[0],
                                 row[1],
                                 row[3],
                                 query_start,
                                 query_end,
                                 row[8],
                                 row[9],
                                 row[11],
                                 query_start > query_end,
                                 ])
        return res
