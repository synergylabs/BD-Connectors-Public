/**************************************************************************
*
* Copyright (C) 2011 Krzysztof Malorny <malornykrzysztof@gmail.com>
*
* Permission is hereby granted, free of charge, to any person obtaining
* a copy of this software and associated documentation files (the
* "Software"), to deal in the Software without restriction, including
* without limitation the rights to use, copy, modify, merge, publish,
* distribute, sublicense, and/or sell copies of the Software, and to
* permit persons to whom the Software is furnished to do so, subject to
* the following conditions:
*
* The above copyright notice and this permission notice shall be included
* in all copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
* EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
* IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
* CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
* TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
* SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*
*********************************************************************/
#include <stdint.h>
#include "bacapp.h"
#include "bacenum.h"
#include "bacdcode.h"
#include "bacdef.h"
#include "wp.h"
#include "wpm.h"

/** @file wpm.c  Encode/Decode BACnet Write Property Multiple APDUs  */

/* decode service */
int wpm_decode_object_id(
    uint8_t * apdu,
    uint16_t apdu_len,
    BACNET_WRITE_PROPERTY_DATA * data)
{
    uint8_t tag_number = 0;
    uint32_t len_value = 0;
    uint32_t object_instance = 0;
    uint16_t object_type = 0;
    uint16_t len = 0;

    if ((apdu) && (apdu_len)) {
        /* Context tag 0 - Object ID */
        len +=
            decode_tag_number_and_value(&apdu[len], &tag_number, &len_value);
        if (tag_number == 0) {
            len +=
                decode_object_id(&apdu[len], &object_type, &object_instance);
            data->object_type = object_type;
            data->object_instance = object_instance;
        } else
            return -1;
    } else
        return -1;

    return (int)len;
}


int wpm_decode_object_property(
    uint8_t * apdu,
    uint16_t apdu_len,
    BACNET_WRITE_PROPERTY_DATA * wp_data)
{
    uint8_t tag_number = 0;
    uint32_t len_value = 0;
    uint32_t ulVal = 0;
    int len = 0, i = 0;


    if ((apdu) && (apdu_len) && (wp_data)) {
        wp_data->array_index = BACNET_ARRAY_ALL;
        wp_data->priority = BACNET_MAX_PRIORITY;
        wp_data->application_data_len = 0;

        /* tag 0 - Property Identifier */
        len +=
            decode_tag_number_and_value(&apdu[len], &tag_number, &len_value);
        if (tag_number == 0) {
            len += decode_enumerated(&apdu[len], len_value, &ulVal);
            wp_data->object_property = ulVal;
        } else
            return -1;

        /* tag 1 - Property Array Index - optional */
        len +=
            decode_tag_number_and_value(&apdu[len], &tag_number, &len_value);
        if (tag_number == 1) {
            len += decode_unsigned(&apdu[len], len_value, &ulVal);
            wp_data->array_index = ulVal;

            len +=
                decode_tag_number_and_value(&apdu[len], &tag_number,
                &len_value);
        }
        /* tag 2 - Property Value */
        if ((tag_number == 2) && (decode_is_opening_tag(&apdu[len - 1]))) {
            len--;
            wp_data->application_data_len =
                bacapp_data_len(&apdu[len], (unsigned)(apdu_len - len),
                wp_data->object_property);
            len++;

            /* copy application data */
            for (i = 0; i < wp_data->application_data_len; i++)
                wp_data->application_data[i] = apdu[len + i];
            len += wp_data->application_data_len;

            len +=
                decode_tag_number_and_value(&apdu[len], &tag_number,
                &len_value);
            /* closing tag 2 */
            if ((tag_number != 2) && (decode_is_closing_tag(&apdu[len - 1])))
                return -1;
        } else
            return -1;

        /* tag 3 - Priority - optional */
        len +=
            decode_tag_number_and_value(&apdu[len], &tag_number, &len_value);
        if (tag_number == 3) {
            len += decode_unsigned(&apdu[len], len_value, &ulVal);
            wp_data->priority = ulVal;
        } else
            len--;
    } else
        return -1;

    return len;
}

int wpm_ack_encode_apdu_init(
    uint8_t * apdu,
    uint8_t invoke_id)
{
    int len = 0;

    if (apdu) {
        apdu[len++] = PDU_TYPE_SIMPLE_ACK;
        apdu[len++] = invoke_id;
        apdu[len++] = SERVICE_CONFIRMED_WRITE_PROP_MULTIPLE;
    }

    return len;
}

int wpm_error_ack_encode_apdu(
    uint8_t * apdu,
    uint8_t invoke_id,
    BACNET_WRITE_PROPERTY_DATA * wp_data)
{
    int len = 0;

    if (apdu) {
        apdu[len++] = PDU_TYPE_ERROR;
        apdu[len++] = invoke_id;
        apdu[len++] = SERVICE_CONFIRMED_WRITE_PROP_MULTIPLE;

        len += encode_opening_tag(&apdu[len], 0);
        len += encode_application_enumerated(&apdu[len], wp_data->error_class);
        len += encode_application_enumerated(&apdu[len], wp_data->error_code);
        len += encode_closing_tag(&apdu[len], 0);

        len += encode_opening_tag(&apdu[len], 1);
        len +=
            encode_context_object_id(&apdu[len], 0, wp_data->object_type,
            wp_data->object_instance);
        len +=
            encode_context_enumerated(&apdu[len], 1, wp_data->object_property);

        if (wp_data->array_index != BACNET_ARRAY_ALL)
            len +=
                encode_context_unsigned(&apdu[len], 2, wp_data->array_index);
        len += encode_closing_tag(&apdu[len], 1);
    }
    return len;
}
