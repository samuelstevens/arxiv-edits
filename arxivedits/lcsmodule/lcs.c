#include <stdlib.h>
#include <stdio.h>
#include <string.h>

/*
gcc arxivedits/lcs/lcs.c -O3 -o arxivedits/lcs/lcs

gcc -c -Wall -Werror -fpic arxivedits/lcs/lcs.c -o arxivedits/lcs/lcs.o
 gcc -shared -o arxivedits/lcs/lcs.so arxivedits/lcs/lcs.o
*/

struct Sequence
{
    char **items;
    int length;
};

struct Cell
{
    int index;
    int length;
    struct Cell *prev;
};

void printSequence(struct Sequence *seq)
{
    printf("%d\n", seq->length);
    for (int i = 0; i < seq->length; i++)
    {
        printf("%s ", seq->items[i]);
    }
    printf("\n");
}

void printCell(struct Cell *cell)
{
    printf("index: %d\t length: %d \tprev: %p\n", cell->index, cell->length, cell->prev);
}

struct Sequence *lcs(struct Sequence *s1, struct Sequence *s2)
{
    struct Sequence *common = malloc(sizeof(struct Sequence));
    common->length = 0;
    common->items = NULL;

    char **seq1 = s1->items;
    char **seq2 = s2->items;

    if (!s1->length || !s2->length)
    {
        return common;
    }

    struct Cell table[s1->length][s2->length];

    for (int i = 0; i < s1->length; i++)
    {
        for (int j = 0; j < s2->length; j++)
        {
            table[i][j].length = 0;
            if (!strcmp(seq1[i], seq2[j]))
            {
                table[i][j].index = j;
                if (i > 0 && j > 0)
                {
                    table[i][j].prev = &table[i - 1][j - 1];
                    table[i][j].length = table[i - 1][j - 1].length + 1;
                }
                else
                {
                    table[i][j].prev = NULL;
                    table[i][j].length = 1;
                }
            }
            else
            {
                table[i][j].index = -1;
                table[i][j].prev = NULL;
                if (i > 0)
                {
                    table[i][j].prev = &table[i - 1][j];
                    table[i][j].length = table[i - 1][j].length;
                }

                if (j > 0)
                {
                    if (table[i][j - 1].length > table[i][j].length)
                    {
                        table[i][j].prev = &table[i][j - 1];
                        table[i][j].length = table[i][j - 1].length;
                    }
                }
            }
        }
    }

    int i = s1->length - 1;
    int j = s2->length - 1;
    struct Cell *cur = &table[i][j];

    common->length = cur->length;
    common->items = malloc(sizeof(char *) * common->length);

    i = cur->length - 1;

    while (cur)
    {
        if (cur->index < 0)
        {
            cur = cur->prev;
            continue;
        }

        common->items[i] = malloc(
            sizeof(char) *
            (strlen(seq2[cur->index]) + 1));

        strcpy(common->items[i], seq2[cur->index]);
        cur = cur->prev;
        i--;
    }
    return common;
}

void freeSequence(struct Sequence *seq)
{
    free(seq);
}

/*
Must be called like so:
./lcs <length 1> <length 2> <sequence> <of> <words1> <sequence2> 
*/
int main(int argc, char **argv)
{
    // char *s1[] = {"First", ",", "we", "validate", "whether", "our", "models", "for", "segmentation", "and", "depth", "estimation", "perform", "well", "on", "the", "synthetic", "test", "set", "of", "our", "SURREAL", "dataset", "."};
    // char *s2[] = {"Segmentation", "and", "depth", "are", "tested", "on", "the", "synthetic", "and", "Human3.6M", "test", "sets", "with", "networks", "pre-trained", "on", "a", "subset", "of", "the", "synthetic", "training", "data", "."};

    if (argc < 3)
    {
        printf("You must provide at least 3 arguments.\n");
        return -1;
    }

    int len1 = atoi(argv[1]);
    int len2 = atoi(argv[2]);

    if (argc < 3 + len1 + len2)
    {
        printf("Sequence lengths must be valid.\n");
        return -1;
    }

    char **s1 = &argv[3];
    char **s2 = &argv[3 + len1];

    struct Sequence seq1;
    seq1.items = s1;
    seq1.length = len1;

    struct Sequence seq2;
    seq2.items = s2;
    seq2.length = len2;

    // printSequence(&seq1);
    // printSequence(&seq2);

    struct Sequence *common = lcs(&seq1, &seq2);

    printSequence(common);
}