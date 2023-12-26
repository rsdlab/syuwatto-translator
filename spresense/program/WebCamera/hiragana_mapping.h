#ifndef HIRAGANA_MAPPING_H
#define HIRAGANA_MAPPING_H

struct HiraganaMapping {
    const char* hiragana;
    int number;
};

extern HiraganaMapping hiraganaMap[];

#ifndef NOT_FOUND
extern const int NOT_FOUND; // NOT_FOUND をここで宣言
#endif

int getHiraganaNumber(const char* hiragana);

#endif // HIRAGANA_MAPPING_H