from massalign.models import TFIDFModel
from massalign.aligners import VicinityDrivenParagraphAligner
from massalign.core import MASSAligner

# Get files to align:
file1 = 'https://raw.githubusercontent.com/samuelstevens/massalign/master/sample_data/test_document_complex.txt'
file2 = 'https://raw.githubusercontent.com/samuelstevens/massalign/master/sample_data/test_document_simple.txt'

# Train model over them:
model = TFIDFModel(
    [file1, file2], 'https://ghpaetzold.github.io/massalign_data/stop_words.txt')

# Get paragraph aligner:
paragraph_aligner = VicinityDrivenParagraphAligner(
    similarity_model=model, acceptable_similarity=0.1)

# Get MASSA aligner:
m = MASSAligner()

# Get paragraphs from the document:
p1s = m.getParagraphsFromDocument(file1)
p2s = m.getParagraphsFromDocument(file2)

# Align paragraphs:
alignments, aligned_paragraphs = m.getParagraphAlignments(
    p1s, p2s, paragraph_aligner)

lengths = [len(a) for a in aligned_paragraphs[0]]
for i in range(min(lengths)):
    print(aligned_paragraphs[0][1][i], '\n',
          aligned_paragraphs[0][0][i], '\n\n')

# Display paragraph alignments:
m.visualizeParagraphAlignments(p1s, p2s, alignments)
# m.visualizeListOfParagraphAlignments(
#     [p1s, p1s], [p2s, p2s], [alignments, alignments])
