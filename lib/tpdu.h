#pragma once

#include "hdlc_frame.h"
#include "tsdu.h"

#include <stdbool.h>
#include <stdint.h>

typedef struct _tpdu_ui_t tpdu_ui_t;

tpdu_ui_t *tpdu_ui_create(void);
void tpdu_ui_destroy(tpdu_ui_t *tpdu);
bool tpdu_ui_push_hdlc_frame(tpdu_ui_t *tpdu, const hdlc_frame_t *hdlc_fr);
tsdu_t *tpdu_ui_get_tsdu(tpdu_ui_t *tpdu);


// old methods
void segmentation_reset(void);
void tpdu_process(const uint8_t *t, int length, int *frame_no);

