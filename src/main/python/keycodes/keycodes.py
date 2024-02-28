# coding: utf-8

# SPDX-License-Identifier: GPL-2.0-or-later

import sys

from keycodes.keycodes_v5 import keycodes_v5
from keycodes.keycodes_v6 import keycodes_v6


class Keycode:

    masked_keycodes = set()
    recorder_alias_to_keycode = dict()
    qmk_id_to_keycode = dict()
    protocol = 0

    def __init__(self, qmk_id, label, tooltip=None, masked=False, printable=None, recorder_alias=None, alias=None):
        self.qmk_id = qmk_id
        self.qmk_id_to_keycode[qmk_id] = self
        self.label = label
        # we cannot embed full CJK fonts due to large size, workaround like this for now
        if sys.platform == "emscripten" and not label.isascii() and qmk_id != "KC_TRNS":
            self.label = qmk_id.replace("KC_", "")

        self.tooltip = tooltip
        # whether this keycode requires another sub-keycode
        self.masked = masked

        # if this is printable keycode, what character does it normally output (i.e. non-shifted state)
        self.printable = printable

        self.alias = [self.qmk_id]
        if alias:
            self.alias += alias

        if recorder_alias:
            for alias in recorder_alias:
                if alias in self.recorder_alias_to_keycode:
                    raise RuntimeError("Misconfigured: two keycodes claim the same alias {}".format(alias))
                self.recorder_alias_to_keycode[alias] = self

        if masked:
            assert qmk_id.endswith("(kc)")
            self.masked_keycodes.add(qmk_id.replace("(kc)", ""))

    @classmethod
    def find(cls, qmk_id):
        # this is to handle cases of qmk_id LCTL(kc) propagated here from find_inner_keycode
        if qmk_id == "kc":
            qmk_id = "KC_NO"
        return KEYCODES_MAP.get(qmk_id)

    @classmethod
    def find_outer_keycode(cls, qmk_id):
        """
        Finds outer keycode, i.e. if it is masked like 0x5Fxx, just return the 0x5F00 portion
        """
        if cls.is_mask(qmk_id):
            qmk_id = qmk_id[:qmk_id.find("(")]
        return cls.find(qmk_id)

    @classmethod
    def find_inner_keycode(cls, qmk_id):
        """
        Finds inner keycode, i.e. if it is masked like 0x5F12, just return the 0x12 portion
        """
        if cls.is_mask(qmk_id):
            qmk_id = qmk_id[qmk_id.find("(")+1:-1]
        return cls.find(qmk_id)

    @classmethod
    def find_by_recorder_alias(cls, alias):
        return cls.recorder_alias_to_keycode.get(alias)

    @classmethod
    def find_by_qmk_id(cls, qmk_id):
        return cls.qmk_id_to_keycode.get(qmk_id)

    @classmethod
    def is_mask(cls, qmk_id):
        return "(" in qmk_id and qmk_id[:qmk_id.find("(")] in cls.masked_keycodes

    @classmethod
    def is_basic(cls, qmk_id):
        return cls.deserialize(qmk_id) < 0x00FF

    @classmethod
    def label(cls, qmk_id):
        keycode = cls.find_outer_keycode(qmk_id)
        if keycode is None:
            return qmk_id
        return keycode.label

    @classmethod
    def tooltip(cls, qmk_id):
        keycode = cls.find_outer_keycode(qmk_id)
        if keycode is None:
            return None
        tooltip = keycode.qmk_id
        if keycode.tooltip:
            tooltip = "{}: {}".format(tooltip, keycode.tooltip)
        return tooltip

    @classmethod
    def serialize(cls, code):
        """ Converts integer keycode to string """
        if cls.protocol == 6:
            masked = keycodes_v6.masked
        else:
            masked = keycodes_v5.masked

        if (code & 0xFF00) not in masked:
            kc = RAWCODES_MAP.get(code)
            if kc is not None:
                return kc.qmk_id
        else:
            outer = RAWCODES_MAP.get(code & 0xFF00)
            inner = RAWCODES_MAP.get(code & 0x00FF)
            if outer is not None and inner is not None:
                return outer.qmk_id.replace("kc", inner.qmk_id)
        return hex(code)

    @classmethod
    def deserialize(cls, val, reraise=False):
        """ Converts string keycode to integer """

        from any_keycode import AnyKeycode

        if isinstance(val, int):
            return val
        if val in cls.qmk_id_to_keycode:
            return cls.resolve(cls.qmk_id_to_keycode[val].qmk_id)
        anykc = AnyKeycode()
        try:
            return anykc.decode(val)
        except Exception:
            if reraise:
                raise
        return 0

    @classmethod
    def normalize(cls, code):
        """ Changes e.g. KC_PERC to LSFT(KC_5) """

        return Keycode.serialize(Keycode.deserialize(code))

    @classmethod
    def resolve(cls, qmk_constant):
        """ Translates a qmk_constant into firmware-specific integer keycode or macro constant """
        if cls.protocol == 6:
            kc = keycodes_v6.kc
        else:
            kc = keycodes_v5.kc

        if qmk_constant not in kc:
            raise RuntimeError("unable to resolve qmk_id={}".format(qmk_constant))
        return kc[qmk_constant]


K = Keycode

KEYCODES_SPECIAL = [
    K("KC_NO", ""),
    K("KC_TRNS", "▽", alias=["KC_TRANSPARENT"]),
]

KEYCODES_BASIC_NUMPAD = [
    K("KC_NUMLOCK", "Num\nLock", recorder_alias=["num lock"], alias=["KC_NLCK"]),
    K("KC_KP_SLASH", "/", alias=["KC_PSLS"]),
    K("KC_KP_ASTERISK", "*", alias=["KC_PAST"]),
    K("KC_KP_MINUS", "-", alias=["KC_PMNS"]),
    K("KC_KP_PLUS", "+", alias=["KC_PPLS"]),
    K("KC_KP_ENTER", "Num\nEnter", alias=["KC_PENT"]),
    K("KC_KP_1", "1", alias=["KC_P1"]),
    K("KC_KP_2", "2", alias=["KC_P2"]),
    K("KC_KP_3", "3", alias=["KC_P3"]),
    K("KC_KP_4", "4", alias=["KC_P4"]),
    K("KC_KP_5", "5", alias=["KC_P5"]),
    K("KC_KP_6", "6", alias=["KC_P6"]),
    K("KC_KP_7", "7", alias=["KC_P7"]),
    K("KC_KP_8", "8", alias=["KC_P8"]),
    K("KC_KP_9", "9", alias=["KC_P9"]),
    K("KC_KP_0", "0", alias=["KC_P0"]),
    K("KC_KP_DOT", ".", alias=["KC_PDOT"]),
    K("KC_KP_EQUAL", "=", alias=["KC_PEQL"]),
    K("KC_KP_COMMA", ",", alias=["KC_PCMM"]),
]

KEYCODES_BASIC_NAV = [
    K("KC_PSCREEN", "Print\nScreen", alias=["KC_PSCR"]),
    K("KC_SCROLLLOCK", "Scroll\nLock", recorder_alias=["scroll lock"], alias=["KC_SLCK", "KC_BRMD"]),
    K("KC_PAUSE", "Pause", recorder_alias=["pause", "break"], alias=["KC_PAUS", "KC_BRK", "KC_BRMU"]),
    K("KC_INSERT", "Insert", recorder_alias=["insert"], alias=["KC_INS"]),
    K("KC_HOME", "Home", recorder_alias=["home"]),
    K("KC_PGUP", "Page\nUp", recorder_alias=["page up"]),
    K("KC_DELETE", "Del", recorder_alias=["delete"], alias=["KC_DEL"]),
    K("KC_END", "End", recorder_alias=["end"]),
    K("KC_PGDOWN", "Page\nDown", recorder_alias=["page down"], alias=["KC_PGDN"]),
    K("KC_RIGHT", "Right", recorder_alias=["right"], alias=["KC_RGHT"]),
    K("KC_LEFT", "Left", recorder_alias=["left"]),
    K("KC_DOWN", "Down", recorder_alias=["down"]),
    K("KC_UP", "Up", recorder_alias=["up"]),
]

KEYCODES_BASIC = [
    K("KC_A", "A", printable="a", recorder_alias=["a"]),
    K("KC_B", "B", printable="b", recorder_alias=["b"]),
    K("KC_C", "C", printable="c", recorder_alias=["c"]),
    K("KC_D", "D", printable="d", recorder_alias=["d"]),
    K("KC_E", "E", printable="e", recorder_alias=["e"]),
    K("KC_F", "F", printable="f", recorder_alias=["f"]),
    K("KC_G", "G", printable="g", recorder_alias=["g"]),
    K("KC_H", "H", printable="h", recorder_alias=["h"]),
    K("KC_I", "I", printable="i", recorder_alias=["i"]),
    K("KC_J", "J", printable="j", recorder_alias=["j"]),
    K("KC_K", "K", printable="k", recorder_alias=["k"]),
    K("KC_L", "L", printable="l", recorder_alias=["l"]),
    K("KC_M", "M", printable="m", recorder_alias=["m"]),
    K("KC_N", "N", printable="n", recorder_alias=["n"]),
    K("KC_O", "O", printable="o", recorder_alias=["o"]),
    K("KC_P", "P", printable="p", recorder_alias=["p"]),
    K("KC_Q", "Q", printable="q", recorder_alias=["q"]),
    K("KC_R", "R", printable="r", recorder_alias=["r"]),
    K("KC_S", "S", printable="s", recorder_alias=["s"]),
    K("KC_T", "T", printable="t", recorder_alias=["t"]),
    K("KC_U", "U", printable="u", recorder_alias=["u"]),
    K("KC_V", "V", printable="v", recorder_alias=["v"]),
    K("KC_W", "W", printable="w", recorder_alias=["w"]),
    K("KC_X", "X", printable="x", recorder_alias=["x"]),
    K("KC_Y", "Y", printable="y", recorder_alias=["y"]),
    K("KC_Z", "Z", printable="z", recorder_alias=["z"]),
    K("KC_1", "!\n1", printable="1", recorder_alias=["1"]),
    K("KC_2", "@\n2", printable="2", recorder_alias=["2"]),
    K("KC_3", "#\n3", printable="3", recorder_alias=["3"]),
    K("KC_4", "$\n4", printable="4", recorder_alias=["4"]),
    K("KC_5", "%\n5", printable="5", recorder_alias=["5"]),
    K("KC_6", "^\n6", printable="6", recorder_alias=["6"]),
    K("KC_7", "&\n7", printable="7", recorder_alias=["7"]),
    K("KC_8", "*\n8", printable="8", recorder_alias=["8"]),
    K("KC_9", "(\n9", printable="9", recorder_alias=["9"]),
    K("KC_0", ")\n0", printable="0", recorder_alias=["0"]),
    K("KC_ENTER", "Enter", recorder_alias=["enter"], alias=["KC_ENT"]),
    K("KC_ESCAPE", "Esc", recorder_alias=["esc"], alias=["KC_ESC"]),
    K("KC_BSPACE", "Bksp", recorder_alias=["backspace"], alias=["KC_BSPC"]),
    K("KC_TAB", "Tab", recorder_alias=["tab"]),
    K("KC_SPACE", "Space", recorder_alias=["space"], alias=["KC_SPC"]),
    K("KC_MINUS", "_\n-", printable="-", recorder_alias=["-"], alias=["KC_MINS"]),
    K("KC_EQUAL", "+\n=", printable="=", recorder_alias=["="], alias=["KC_EQL"]),
    K("KC_LBRACKET", "{\n[", printable="[", recorder_alias=["["], alias=["KC_LBRC"]),
    K("KC_RBRACKET", "}\n]", printable="]", recorder_alias=["]"], alias=["KC_RBRC"]),
    K("KC_BSLASH", "|\n\\", printable="\\", recorder_alias=["\\"], alias=["KC_BSLS"]),
    K("KC_SCOLON", ":\n;", printable=";", recorder_alias=[";"], alias=["KC_SCLN"]),
    K("KC_QUOTE", "\"\n'", printable="'", recorder_alias=["'"], alias=["KC_QUOT"]),
    K("KC_GRAVE", "~\n`", printable="`", recorder_alias=["`"], alias=["KC_GRV", "KC_ZKHK"]),
    K("KC_COMMA", "<\n,", printable=",", recorder_alias=[","], alias=["KC_COMM"]),
    K("KC_DOT", ">\n.", printable=".", recorder_alias=["."]),
    K("KC_SLASH", "?\n/", printable="/", recorder_alias=["/"], alias=["KC_SLSH"]),
    K("KC_CAPSLOCK", "Caps\nLock", recorder_alias=["caps lock"], alias=["KC_CLCK", "KC_CAPS"]),
    K("KC_F1", "F1", recorder_alias=["f1"]),
    K("KC_F2", "F2", recorder_alias=["f2"]),
    K("KC_F3", "F3", recorder_alias=["f3"]),
    K("KC_F4", "F4", recorder_alias=["f4"]),
    K("KC_F5", "F5", recorder_alias=["f5"]),
    K("KC_F6", "F6", recorder_alias=["f6"]),
    K("KC_F7", "F7", recorder_alias=["f7"]),
    K("KC_F8", "F8", recorder_alias=["f8"]),
    K("KC_F9", "F9", recorder_alias=["f9"]),
    K("KC_F10", "F10", recorder_alias=["f10"]),
    K("KC_F11", "F11", recorder_alias=["f11"]),
    K("KC_F12", "F12", recorder_alias=["f12"]),

    K("KC_APPLICATION", "Menu", recorder_alias=["menu", "left menu", "right menu"], alias=["KC_APP"]),
    K("KC_LCTRL", "LCtrl", recorder_alias=["left ctrl", "ctrl"], alias=["KC_LCTL"]),
    K("KC_LSHIFT", "LShift", recorder_alias=["left shift", "shift"], alias=["KC_LSFT"]),
    K("KC_LALT", "LAlt", recorder_alias=["alt"], alias=["KC_LOPT"]),
    K("KC_LGUI", "LGui", recorder_alias=["left windows", "windows"], alias=["KC_LCMD", "KC_LWIN"]),
    K("KC_RCTRL", "RCtrl", recorder_alias=["right ctrl"], alias=["KC_RCTL"]),
    K("KC_RSHIFT", "RShift", recorder_alias=["right shift"], alias=["KC_RSFT"]),
    K("KC_RALT", "RAlt", alias=["KC_ALGR", "KC_ROPT"]),
    K("KC_RGUI", "RGui", recorder_alias=["right windows"], alias=["KC_RCMD", "KC_RWIN"]),
]

KEYCODES_BASIC.extend(KEYCODES_BASIC_NUMPAD)
KEYCODES_BASIC.extend(KEYCODES_BASIC_NAV)

KEYCODES_SHIFTED = [
    K("KC_TILD", "~"),
    K("KC_EXLM", "!"),
    K("KC_AT", "@"),
    K("KC_HASH", "#"),
    K("KC_DLR", "$"),
    K("KC_PERC", "%"),
    K("KC_CIRC", "^"),
    K("KC_AMPR", "&"),
    K("KC_ASTR", "*"),
    K("KC_LPRN", "("),
    K("KC_RPRN", ")"),
    K("KC_UNDS", "_"),
    K("KC_PLUS", "+"),
    K("KC_LCBR", "{"),
    K("KC_RCBR", "}"),
    K("KC_LT", "<"),
    K("KC_GT", ">"),
    K("KC_COLN", ":"),
    K("KC_PIPE", "|"),
    K("KC_QUES", "?"),
    K("KC_DQUO", '"'),
]

KEYCODES_ISO = [
    K("KC_NONUS_HASH", "~\n#", "Non-US # and ~", alias=["KC_NUHS"]),
    K("KC_NONUS_BSLASH", "|\n\\", "Non-US \\ and |", alias=["KC_NUBS"]),
    K("KC_RO", "_\n\\", "JIS \\ and _", alias=["KC_INT1"]),
    K("KC_KANA", "カタカナ\nひらがな", "JIS Katakana/Hiragana", alias=["KC_INT2"]),
    K("KC_JYEN", "|\n¥", alias=["KC_INT3"]),
    K("KC_HENK", "変換", "JIS Henkan", alias=["KC_INT4"]),
    K("KC_MHEN", "無変換", "JIS Muhenkan", alias=["KC_INT5"]),
]

KEYCODES_ISO_KR = [
    K("KC_LANG1", "한영\nかな", "Korean Han/Yeong / JP Mac Kana", alias=["KC_HAEN"]),
    K("KC_LANG2", "漢字\n英数", "Korean Hanja / JP Mac Eisu", alias=["KC_HANJ"]),
]

KEYCODES_ISO.extend(KEYCODES_ISO_KR)

KEYCODES_LAYERS = []
RESET_KEYCODE = "RESET"

KEYCODES_BOOT = [
    K("RESET", "Reset", "Reboot to bootloader")
]

KEYCODES_MODIFIERS = [
    K("OSM(MOD_LSFT)", "OSM\nLSft", "按下时激活左Shift键"),
    K("OSM(MOD_LCTL)", "OSM\nLCtl", "按下时激活左Ctl键"),
    K("OSM(MOD_LALT)", "OSM\nLAlt", "按下时激活左Alt键"),
    K("OSM(MOD_LGUI)", "OSM\nLGUI", "按下时激活左GUI键"),
    K("OSM(MOD_RSFT)", "OSM\nRSft", "按下时激活右Shift键"),
    K("OSM(MOD_RCTL)", "OSM\nRCtl", "按下时激活右Shift键"),
    K("OSM(MOD_RALT)", "OSM\nRAlt", "按下时激活右Shift键"),
    K("OSM(MOD_RGUI)", "OSM\nRGUI", "按下时激活右Shift键"),
    K("OSM(MOD_LCTL|MOD_LSFT)", "OSM\nCS", "按下激活左Ctl键和左Shift键"),
    K("OSM(MOD_LCTL|MOD_LALT)", "OSM\nCA", "按下激活左Ctl键和左Alt键"),
    K("OSM(MOD_LCTL|MOD_LGUI)", "OSM\nCG", "按下激活左Ctl键和左GUI键"),
    K("OSM(MOD_LSFT|MOD_LALT)", "OSM\nSA", "按下激活左Shift键和左Alt键"),
    K("OSM(MOD_LSFT|MOD_LGUI)", "OSM\nSG", "按下激活左Shift键和左GUI键"),
    K("OSM(MOD_LALT|MOD_LGUI)", "OSM\nAG", "按下激活左Alt键和左Shift键"),
    K("OSM(MOD_RCTL|MOD_RSFT)", "OSM\nRCS", "按下激活右Ctl键和右Shift键"),
    K("OSM(MOD_RCTL|MOD_RALT)", "OSM\nRCA", "按下激活右Ctl键和右Alt键"),
    K("OSM(MOD_RCTL|MOD_RGUI)", "OSM\nRCG", "按下激活右Ctl键和右GUI键"),
    K("OSM(MOD_RSFT|MOD_RALT)", "OSM\nRSA", "按下激活右Shift键和右Alt键"),
    K("OSM(MOD_RSFT|MOD_RGUI)", "OSM\nRSG", "按下激活右Alt键和右Shift键"),
    K("OSM(MOD_RALT|MOD_RGUI)", "OSM\nRAG", "按下激活右Alt键和右GUI键"),
    K("OSM(MOD_LCTL|MOD_LSFT|MOD_LGUI)", "OSM\nCSG", "按下激活左Ctl键，左Shift, 左GUI键"),
    K("OSM(MOD_LCTL|MOD_LALT|MOD_LGUI)", "OSM\nCAG", "按下激活左Ctl键，左Alt, 左GUI键"),
    K("OSM(MOD_LSFT|MOD_LALT|MOD_LGUI)", "OSM\nSAG", "按下激活左Shift键，左Alt, 左GUI键"),
    K("OSM(MOD_RCTL|MOD_RSFT|MOD_RGUI)", "OSM\nRCSG", "按下激活右Ctl键，右Shift, 右GUI键"),
    K("OSM(MOD_RCTL|MOD_RALT|MOD_RGUI)", "OSM\nRCAG", "按下激活右Ctl键，右Alt, 右GUI键"),
    K("OSM(MOD_RSFT|MOD_RALT|MOD_RGUI)", "OSM\nRSAG", "按下激活右Shift键，右Alt, 右GUI键"),
    K("OSM(MOD_MEH)", "OSM\nMeh", "按下激活左Ctl键，左Shift, 左Alt键"),
    K("OSM(MOD_HYPR)", "OSM\nHyper", "按下激活左Ctl键，左Shift, 左Alt键, 左GUI键"),
    K("OSM(MOD_RCTL|MOD_RSFT|MOD_RALT)", "OSM\nRMeh", "按下激活右Ctl键，右Shift, 右Alt键"),
    K("OSM(MOD_RCTL|MOD_RSFT|MOD_RALT|MOD_RGUI)", "OSM\nRHyp", "按下激活右Ctl键，右Shift, 右Alt键, 右GUI键"),

    K("LSFT(kc)", "LSft\n(kc)", masked=True),
    K("LCTL(kc)", "LCtl\n(kc)", masked=True),
    K("LALT(kc)", "LAlt\n(kc)", masked=True),
    K("LGUI(kc)", "LGui\n(kc)", masked=True),
    K("RSFT(kc)", "RSft\n(kc)", masked=True),
    K("RCTL(kc)", "RCtl\n(kc)", masked=True),
    K("RALT(kc)", "RAlt\n(kc)", masked=True),
    K("RGUI(kc)", "RGui\n(kc)", masked=True),
    K("C_S(kc)", "LCS\n(kc)", "LCTL + LSFT", masked=True, alias=["LCS(kc)"]),
    K("LCA(kc)", "LCA\n(kc)", "LCTL + LALT", masked=True),
    K("LCG(kc)", "LCG\n(kc)", "LCTL + LGUI", masked=True),
    K("LSA(kc)", "LSA\n(kc)", "LSFT + LALT", masked=True),
    K("SGUI(kc)", "LSG\n(kc)", "LGUI + LSFT", masked=True, alias=["LSG(kc)"]),
    K("LCAG(kc)", "LCAG\n(kc)", "LCTL + LALT + LGUI", masked=True),
    K("RCG(kc)", "RCG\n(kc)", "RCTL + RGUI", masked=True),
    K("MEH(kc)", "Meh\n(kc)", "LCTL + LSFT + LALT", masked=True),
    K("HYPR(kc)", "Hyper\n(kc)", "LCTL + LSFT + LALT + LGUI", masked=True),

    K("LSFT_T(kc)", "LSft_T\n(kc)", "长按触发左Shift键, 单击触发kc键", masked=True),
    K("LCTL_T(kc)", "LCtl_T\n(kc)", "长按触发左Ctl键, 单击触发kc键", masked=True),
    K("LALT_T(kc)", "LAlt_T\n(kc)", "长按触发左Alt键, 单击触发kc键", masked=True),
    K("LGUI_T(kc)", "LGui_T\n(kc)", "长按触发左Gui键, 单击触发kc键", masked=True),
    K("RSFT_T(kc)", "RSft_T\n(kc)", "长按触发右Shift键, 单击触发kc键", masked=True),
    K("RCTL_T(kc)", "RCtl_T\n(kc)", "长按触发右Ctl键, 单击触发kc键", masked=True),
    K("RALT_T(kc)", "RAlt_T\n(kc)", "长按触发右Alt键, 单击触发kc键", masked=True),
    K("RGUI_T(kc)", "RGui_T\n(kc)", "长按触发右Gui键, 单击触发kc键", masked=True),
    K("C_S_T(kc)", "LCS_T\n(kc)", "长按触发左Ctl键和左Shift键, 单击触发kc键", masked=True, alias=["LCS_T(kc)"] ),
    K("LCA_T(kc)", "LCA_T\n(kc)", "长按触发左Ctl键和左Alt键, 单击触发kc键", masked=True),
    K("LCG_T(kc)", "LCG_T\n(kc)", "长按触发左Ctl键和左Gui键, 单击触发kc键", masked=True),
    K("LSA_T(kc)", "LSA_T\n(kc)", "长按触发左Shift键和左Alt键, 单击触发kc键", masked=True),
    K("SGUI_T(kc)", "LSG_T\n(kc)", "按触发左Shift键和左Gui键, 单击触发kc键", masked=True, alias=["LSG_T(kc)"]),
    K("LCAG_T(kc)", "LCAG_T\n(kc)", "长按触发左Ctl键、左Alt键和左Gui键, 单击触发kc键", masked=True),
    K("RCG_T(kc)", "RCG_T\n(kc)", "长按触发右Ctl键和右Gui键, 单击触发kc键", masked=True),
    K("RCAG_T(kc)", "RCAG_T\n(kc)", "按触发右Ctl键、右Alt键和右Gui键, 单击触发kc键", masked=True),
    K("MEH_T(kc)", "Meh_T\n(kc)", "长按触发左Ctl键、左Shift键和左Alt键, 单击触发kc键", masked=True),
    K("ALL_T(kc)", "ALL_T\n(kc)", "长按触发左Ctl键、左Shift键、左Alt键和左Gui键, 单击触发kc键", masked=True),

    K("KC_GESC", "~\nEsc", "在正常情况下作为Esc键使用，但当Shift键或GUI键被按下时作为~键使用"),
    K("KC_LSPO", "LS\n(", "长按触发左Shift，单击触发("),
    K("KC_RSPC", "RS\n)", "长按触发右Shift，单击触发)"),
    K("KC_LCPO", "LC\n(", "长按触发左Ctl，单击触发("),
    K("KC_RCPC", "RC\n)", "长按触发右Ctl，单击触发)"),
    K("KC_LAPO", "LA\n(", "长按触发左Alt，单击触发("),
    K("KC_RAPC", "RA\n)", "长按触发右Alt，单击触发)"),
    K("KC_SFTENT", "RS\nEnter", "长按触发右Shift，单击触发Enter"),
]

KEYCODES_QUANTUM = [
    K("MAGIC_SWAP_CONTROL_CAPSLOCK", "Swap\nCtrl\nCaps", "交换Caps Lock键和左Control键的位置", alias=["CL_SWAP"]),
    K("MAGIC_UNSWAP_CONTROL_CAPSLOCK", "Unswap\nCtrl\nCaps", "交换大写锁定键（Caps Lock）和左控制键（Left Control）的位置", alias=["CL_NORM"]),
    K("MAGIC_CAPSLOCK_TO_CONTROL", "Caps\nto\nCtrl", "将大写锁定键（Caps Lock）视为控制键（Control）使用", alias=["CL_CTRL"]),
    K("MAGIC_UNCAPSLOCK_TO_CONTROL", "Caps\nnot to\nCtrl", "停止将大写锁定键（Caps Lock）作为控制键（Control）使用", alias=["CL_CAPS"]),
    K("MAGIC_SWAP_LCTL_LGUI", "Swap\nLCtl\nLGui", "交换左控制键（Left Control）和GUI键", alias=["LCG_SWP"]),
    K("MAGIC_UNSWAP_LCTL_LGUI", "Unswap\nLCtl\nLGui", "取消交换左控制键（Left Control）和GUI键", alias=["LCG_NRM"]),
    K("MAGIC_SWAP_RCTL_RGUI", "Swap\nRCtl\nRGui", "交换右控制键（Right Control）和GUI键", alias=["RCG_SWP"]),
    K("MAGIC_UNSWAP_RCTL_RGUI", "Unswap\nRCtl\nRGui", "取消交换右控制键（Right Control）和GUI键", alias=["RCG_NRM"]),
    K("MAGIC_SWAP_CTL_GUI", "Swap\nCtl\nGui", "在两侧（即左侧和右侧）都交换控制键（Control）和GUI键", alias=["CG_SWAP"]),
    K("MAGIC_UNSWAP_CTL_GUI", "Unswap\nCtl\nGui", "取消在两侧（左侧和右侧）控制键（Control）和GUI键", alias=["CG_NORM"]),
    K("MAGIC_TOGGLE_CTL_GUI", "Toggle\nCtl\nGui", "切换两侧（左侧和右侧）控制键（Control）和GUI键", alias=["CG_TOGG"]),
    K("MAGIC_SWAP_LALT_LGUI", "Swap\nLAlt\nLGui", "交换左Alt键和GUI键的位置", alias=["LAG_SWP"]),
    K("MAGIC_UNSWAP_LALT_LGUI", "Unswap\nLAlt\nLGui", "取消交换左Alt键和GUI键的位置", alias=["LAG_NRM"]),
    K("MAGIC_SWAP_RALT_RGUI", "Swap\nRAlt\nRGui", "交换右Alt键和GUI键的位置", alias=["RAG_SWP"]),
    K("MAGIC_UNSWAP_RALT_RGUI", "Unswap\nRAlt\nRGui", "取消交换右Alt键和GUI键的位置", alias=["RAG_NRM"]),
    K("MAGIC_SWAP_ALT_GUI", "Swap\nAlt\nGui", "在键盘的两侧（左侧和右侧）都交换Alt键和GUI键的位置", alias=["AG_SWAP"]),
    K("MAGIC_UNSWAP_ALT_GUI", "Unswap\nAlt\nGui", "取消在键盘的两侧（左侧和右侧）都交换Alt键和GUI键的位置", alias=["AG_NORM"]),
    K("MAGIC_TOGGLE_ALT_GUI", "Toggle\nAlt\nGui", "切换两侧（左侧和右侧）Alt键和GUI键的交换状态", alias=["AG_TOGG"]),
    K("MAGIC_NO_GUI", "GUI\nOff", "禁用GUI键", alias=["GUI_OFF"]),
    K("MAGIC_UNNO_GUI", "GUI\nOn", "开启GUI键, alias=["GUI_ON"]),
    K("MAGIC_SWAP_GRAVE_ESC", "Swap\n`\nEsc", "Swap ` and Escape", alias=["GE_SWAP"]),
    K("MAGIC_UNSWAP_GRAVE_ESC", "Unswap\n`\nEsc", "Unswap ` and Escape", alias=["GE_NORM"]),
    K("MAGIC_SWAP_BACKSLASH_BACKSPACE", "Swap\n\\\nBS", "Swap \\ and Backspace", alias=["BS_SWAP"]),
    K("MAGIC_UNSWAP_BACKSLASH_BACKSPACE", "Unswap\n\\\nBS", "Unswap \\ and Backspace", alias=["BS_NORM"]),
    K("MAGIC_HOST_NKRO", "NKRO\nOn", "启用全键无冲", alias=["NK_ON"]),
    K("MAGIC_UNHOST_NKRO", "NKRO\nOff", "禁用全键无冲", alias=["NK_OFF"]),
    K("MAGIC_TOGGLE_NKRO", "NKRO\nToggle", "切换到全键无冲", alias=["NK_TOGG"]),
    K("MAGIC_EE_HANDS_LEFT", "EEH\nLeft", "将分体键盘的主半部分设置为左手侧（对于EE_HANDS",
      alias=["EH_LEFT"]),
    K("MAGIC_EE_HANDS_RIGHT", "EEH\nRight", "将分体键盘的主半部分设置为右手侧（对于EE_HANDS)",
      alias=["EH_RGHT"]),

    K("AU_ON", "Audio\nON", "打开音频功能"),
    K("AU_OFF", "Audio\nOFF", "关闭音频功能"),
    K("AU_TOG", "Audio\nToggle", "切换音频功能"),
    K("CLICKY_TOGGLE", "Clicky\nToggle", "切换音频滴答模式", alias=["CK_TOGG"]),
    K("CLICKY_UP", "Clicky\nUp", "增加滴答频率", alias=["CK_UP"]),
    K("CLICKY_DOWN", "Clicky\nDown", "减少滴答频率", alias=["CK_DOWN"]),
    K("CLICKY_RESET", "Clicky\nReset", "将频率重置为默认值", alias=["CK_RST"]),
    K("MU_ON", "Music\nOn", "开启音乐模式"),
    K("MU_OFF", "Music\nOff", "关闭音乐模式"),
    K("MU_TOG", "Music\nToggle", "切换音乐模式"),
    K("MU_MOD", "Music\nCycle", "按顺序循环切换不同的音乐模式"),

    K("HPT_ON", "Haptic\nOn", "开启触觉反馈"),
    K("HPT_OFF", "Haptic\nOff", "关闭触觉反馈"),
    K("HPT_TOG", "Haptic\nToggle", "切换触觉反馈的开启/关闭状态"),
    K("HPT_RST", "Haptic\nReset", "将触觉反馈配置重置为默认设置"),
    K("HPT_FBK", "Haptic\nFeed\nback", "切换按键反馈发生在按下、释放或两者都发生时"),
    K("HPT_BUZ", "Haptic\nBuzz", "切换电磁阀嗡嗡声的开启/关闭状态"),
    K("HPT_MODI", "Haptic\nNext", "切换到下一个DRV2605L波形"),
    K("HPT_MODD", "Haptic\nPrev", "切换到上一个DRV2605L波形"),
    K("HPT_CONT", "Haptic\nCont.", "Toggle continuous haptic mode on/off"),
    K("HPT_CONI", "Haptic\n+", "Increase DRV2605L continous haptic strength"),
    K("HPT_COND", "Haptic\n-", "Decrease DRV2605L continous haptic strength"),
    K("HPT_DWLI", "Haptic\nDwell+", "增加电磁阀停留时间"),
    K("HPT_DWLD", "Haptic\nDwell-", "减少电磁阀停留时间"),

    K("KC_ASDN", "Auto-\nshift\nDown", "降低Auto Shift按下判断时间"),
    K("KC_ASUP", "Auto-\nshift\nUp", "增加Auto Shift弹起判断时间"),
    K("KC_ASRP", "Auto-\nshift\nReport", "报告当前Auto Shift 判断时间"),
    K("KC_ASON", "Auto-\nshift\nOn", "开启Auto Shift功能"),
    K("KC_ASOFF", "Auto-\nshift\nOff", "关闭Auto Shift功能"),
    K("KC_ASTG", "Auto-\nshift\nToggle", "切换Auto Shift功能的状态"),

    K("CMB_ON", "Combo\nOn", "开启组合键Combo功能"),
    K("CMB_OFF", "Combo\nOff", "关闭组合键Combo功能"),
    K("CMB_TOG", "Combo\nToggle", "切换组合键Combo开启关闭状态"),
]

KEYCODES_BACKLIGHT = [
    K("BL_TOGG", "BL\nToggle", "打开或关闭背光灯"),
    K("BL_STEP", "BL\nCycle", "循环切换背光级别"),
    K("BL_BRTG", "BL\nBreath", "切换背光呼吸效果"),
    K("BL_ON", "BL On", "将背光设置为最大亮度"),
    K("BL_OFF", "BL Off", "关闭背光灯"),
    K("BL_INC", "BL +", "增加背光亮度级别"),
    K("BL_DEC", "BL - ", "降低背光亮度级别"),

    K("RGB_TOG", "RGB\nToggle", "将 RGB 灯光切换为开启或关闭状态"),
    K("RGB_MOD", "RGB\nMode +", "下一个 RGB 模式"),
    K("RGB_RMOD", "RGB\nMode -", "上一个 RGB 模式"),
    K("RGB_HUI", "Hue +", "增加色调"),
    K("RGB_HUD", "Hue -", "减少色调"),
    K("RGB_SAI", "Sat +", "增加饱和度"),
    K("RGB_SAD", "Sat -", "减少饱和度"),
    K("RGB_VAI", "Bright +", "增加亮度"),
    K("RGB_VAD", "Bright -", "减少亮度"),
    K("RGB_SPI", "Effect +", "增加 RGB 效果速度"),
    K("RGB_SPD", "Effect -", "减少 RGB 效果速度"),
    K("RGB_M_P", "RGB\nMode P", "RGB 模式已设置为: 普通"),
    K("RGB_M_B", "RGB\nMode B", "RGB 模式已设置为: 呼吸"),
    K("RGB_M_R", "RGB\nMode R", "RGB 模式已设置为: 彩虹"),
    K("RGB_M_SW", "RGB\nMode SW", "RGB 模式已设置为: 旋转"),
    K("RGB_M_SN", "RGB\nMode SN", "RGB 模式已设置为: 蛇形"),
    K("RGB_M_K", "RGB\nMode K", "RGB 模式已设置为: 骑士侠"),
    K("RGB_M_X", "RGB\nMode X", "RGB 模式已设置为: 圣诞节"),
    K("RGB_M_G", "RGB\nMode G", "RGB 模式已设置为: 渐变"),
    K("RGB_M_T", "RGB\nMode T", "RGB 模式已设置为: 测试"),
]

KEYCODES_MEDIA = [
    K("KC_F13", "F13"),
    K("KC_F14", "F14"),
    K("KC_F15", "F15"),
    K("KC_F16", "F16"),
    K("KC_F17", "F17"),
    K("KC_F18", "F18"),
    K("KC_F19", "F19"),
    K("KC_F20", "F20"),
    K("KC_F21", "F21"),
    K("KC_F22", "F22"),
    K("KC_F23", "F23"),
    K("KC_F24", "F24"),

    K("KC_PWR", "Power", "关闭", alias=["KC_SYSTEM_POWER"]),
    K("KC_SLEP", "Sleep", "休眠", alias=["KC_SYSTEM_SLEEP"]),
    K("KC_WAKE", "Wake", "唤醒", alias=["KC_SYSTEM_WAKE"]),
    K("KC_EXEC", "Exec", "退出", alias=["KC_EXECUTE"]),
    K("KC_HELP", "Help"),
    K("KC_SLCT", "Select", alias=["KC_SELECT"]),
    K("KC_STOP", "Stop"),
    K("KC_AGIN", "Again", alias=["KC_AGAIN"]),
    K("KC_UNDO", "Undo"),
    K("KC_CUT", "Cut"),
    K("KC_COPY", "Copy"),
    K("KC_PSTE", "Paste", alias=["KC_PASTE"]),
    K("KC_FIND", "Find"),

    K("KC_CALC", "Calc", "启动计算器 (Windows)", alias=["KC_CALCULATOR"]),
    K("KC_MAIL", "Mail", "启动邮箱 (Windows)"),
    K("KC_MSEL", "Media\nPlayer", "启动媒体播放器 (Windows)", alias=["KC_MEDIA_SELECT"]),
    K("KC_MYCM", "My\nPC", "启动我的电脑 (Windows)", alias=["KC_MY_COMPUTER"]),
    K("KC_WSCH", "Browser\nSearch", "浏览器搜索 (Windows)", alias=["KC_WWW_SEARCH"]),
    K("KC_WHOM", "Browser\nHome", "浏览器主页 (Windows)", alias=["KC_WWW_HOME"]),
    K("KC_WBAK", "Browser\nBack", "浏览器返回 (Windows)", alias=["KC_WWW_BACK"]),
    K("KC_WFWD", "Browser\nForward", "浏览器前进 (Windows)", alias=["KC_WWW_FORWARD"]),
    K("KC_WSTP", "Browser\nStop", "浏览器停止 (Windows)", alias=["KC_WWW_STOP"]),
    K("KC_WREF", "Browser\nRefresh", "浏览器刷新 (Windows)", alias=["KC_WWW_REFRESH"]),
    K("KC_WFAV", "Browser\nFav.", "浏览器收藏夹 (Windows)", alias=["KC_WWW_FAVORITES"]),
    K("KC_BRIU", "Bright.\nUp", "增加屏幕亮度（笔记本电脑）", alias=["KC_BRIGHTNESS_UP"]),
    K("KC_BRID", "Bright.\nDown", "降低屏幕亮度（笔记本电脑）", alias=["KC_BRIGHTNESS_DOWN"]),

    K("KC_MPRV", "Media\nPrev", "Previous Track", alias=["KC_MEDIA_PREV_TRACK"]),
    K("KC_MNXT", "Media\nNext", "Next Track", alias=["KC_MEDIA_NEXT_TRACK"]),
    K("KC_MUTE", "Mute", "Mute Audio", alias=["KC_AUDIO_MUTE"]),
    K("KC_VOLD", "Vol -", "Volume Down", alias=["KC_AUDIO_VOL_DOWN"]),
    K("KC_VOLU", "Vol +", "Volume Up", alias=["KC_AUDIO_VOL_UP"]),
    K("KC__VOLDOWN", "Vol -\nAlt", "Volume Down Alternate"),
    K("KC__VOLUP", "Vol +\nAlt", "Volume Up Alternate"),
    K("KC_MSTP", "Media\nStop", alias=["KC_MEDIA_STOP"]),
    K("KC_MPLY", "Media\nPlay", "Play/Pause", alias=["KC_MEDIA_PLAY_PAUSE"]),
    K("KC_MRWD", "Prev\nTrack\n(macOS)", "Previous Track / Rewind (macOS)", alias=["KC_MEDIA_REWIND"]),
    K("KC_MFFD", "Next\nTrack\n(macOS)", "Next Track / Fast Forward (macOS)", alias=["KC_MEDIA_FAST_FORWARD"]),
    K("KC_EJCT", "Eject", "Eject (macOS)", alias=["KC_MEDIA_EJECT"]),

    K("KC_MS_U", "Mouse\nUp", "鼠标光标向上", alias=["KC_MS_UP"]),
    K("KC_MS_D", "Mouse\nDown", "鼠标光标向下", alias=["KC_MS_DOWN"]),
    K("KC_MS_L", "Mouse\nLeft", "鼠标光标向左", alias=["KC_MS_LEFT"]),
    K("KC_MS_R", "Mouse\nRight", "鼠标光标向右", alias=["KC_MS_RIGHT"]),
    K("KC_BTN1", "Mouse\n1", "Mouse Button 1", alias=["KC_MS_BTN1"]),
    K("KC_BTN2", "Mouse\n2", "Mouse Button 2", alias=["KC_MS_BTN2"]),
    K("KC_BTN3", "Mouse\n3", "Mouse Button 3", alias=["KC_MS_BTN3"]),
    K("KC_BTN4", "Mouse\n4", "Mouse Button 4", alias=["KC_MS_BTN4"]),
    K("KC_BTN5", "Mouse\n5", "Mouse Button 5", alias=["KC_MS_BTN5"]),
    K("KC_WH_U", "Mouse\nWheel\nUp", alias=["KC_MS_WH_UP"]),
    K("KC_WH_D", "Mouse\nWheel\nDown", alias=["KC_MS_WH_DOWN"]),
    K("KC_WH_L", "Mouse\nWheel\nLeft", alias=["KC_MS_WH_LEFT"]),
    K("KC_WH_R", "Mouse\nWheel\nRight", alias=["KC_MS_WH_RIGHT"]),
    K("KC_ACL0", "Mouse\nAccel\n0", "将鼠标加速度设置为 0", alias=["KC_MS_ACCEL0"]),
    K("KC_ACL1", "Mouse\nAccel\n1", "将鼠标加速度设置为 1", alias=["KC_MS_ACCEL1"]),
    K("KC_ACL2", "Mouse\nAccel\n2", "将鼠标加速度设置为 2", alias=["KC_MS_ACCEL2"]),

    K("KC_LCAP", "Locking\nCaps", "锁定大小写锁", alias=["KC_LOCKING_CAPS"]),
    K("KC_LNUM", "Locking\nNum", "锁定数字锁", alias=["KC_LOCKING_NUM"]),
    K("KC_LSCR", "Locking\nScroll", "锁定滚动锁", alias=["KC_LOCKING_SCROLL"]),
]

KEYCODES_TAP_DANCE = []

KEYCODES_USER = []

KEYCODES_MACRO = []

KEYCODES_MACRO_BASE = [
    K("DYN_REC_START1", "DM1\nRec", "动态宏1记录开始", alias=["DM_REC1"]),
    K("DYN_REC_START2", "DM2\nRec", "动态宏2记录开始", alias=["DM_REC2"]),
    K("DYN_REC_STOP", "DM Rec\nStop", "动态宏录制停止", alias=["DM_RSTP"]),
    K("DYN_MACRO_PLAY1", "DM1\nPlay", "播放动态宏1", alias=["DM_PLY1"]),
    K("DYN_MACRO_PLAY2", "DM2\nPlay", "播放动态宏2", alias=["DM_PLY2"]),
]

KEYCODES_MIDI = []

KEYCODES_MIDI_BASIC = [
    K("MI_C", "ᴹᴵᴰᴵ\nC", "Midi send note C"),
    K("MI_Cs", "ᴹᴵᴰᴵ\nC#/Dᵇ", "Midi send note C#/Dᵇ", alias=["MI_Db"]),
    K("MI_D", "ᴹᴵᴰᴵ\nD", "Midi send note D"),
    K("MI_Ds", "ᴹᴵᴰᴵ\nD#/Eᵇ", "Midi send note D#/Eᵇ", alias=["MI_Eb"]),
    K("MI_E", "ᴹᴵᴰᴵ\nE", "Midi send note E"),
    K("MI_F", "ᴹᴵᴰᴵ\nF", "Midi send note F"),
    K("MI_Fs", "ᴹᴵᴰᴵ\nF#/Gᵇ", "Midi send note F#/Gᵇ", alias=["MI_Gb"]),
    K("MI_G", "ᴹᴵᴰᴵ\nG", "Midi send note G"),
    K("MI_Gs", "ᴹᴵᴰᴵ\nG#/Aᵇ", "Midi send note G#/Aᵇ", alias=["MI_Ab"]),
    K("MI_A", "ᴹᴵᴰᴵ\nA", "Midi send note A"),
    K("MI_As", "ᴹᴵᴰᴵ\nA#/Bᵇ", "Midi send note A#/Bᵇ", alias=["MI_Bb"]),
    K("MI_B", "ᴹᴵᴰᴵ\nB", "Midi send note B"),

    K("MI_C_1", "ᴹᴵᴰᴵ\nC₁", "Midi send note C₁"),
    K("MI_Cs_1", "ᴹᴵᴰᴵ\nC#₁/Dᵇ₁", "Midi send note C#₁/Dᵇ₁", alias=["MI_Db_1"]),
    K("MI_D_1", "ᴹᴵᴰᴵ\nD₁", "Midi send note D₁"),
    K("MI_Ds_1", "ᴹᴵᴰᴵ\nD#₁/Eᵇ₁", "Midi send note D#₁/Eᵇ₁", alias=["MI_Eb_1"]),
    K("MI_E_1", "ᴹᴵᴰᴵ\nE₁", "Midi send note E₁"),
    K("MI_F_1", "ᴹᴵᴰᴵ\nF₁", "Midi send note F₁"),
    K("MI_Fs_1", "ᴹᴵᴰᴵ\nF#₁/Gᵇ₁", "Midi send note F#₁/Gᵇ₁", alias=["MI_Gb_1"]),
    K("MI_G_1", "ᴹᴵᴰᴵ\nG₁", "Midi send note G₁"),
    K("MI_Gs_1", "ᴹᴵᴰᴵ\nG#₁/Aᵇ₁", "Midi send note G#₁/Aᵇ₁", alias=["MI_Ab_1"]),
    K("MI_A_1", "ᴹᴵᴰᴵ\nA₁", "Midi send note A₁"),
    K("MI_As_1", "ᴹᴵᴰᴵ\nA#₁/Bᵇ₁", "Midi send note A#₁/Bᵇ₁", alias=["MI_Bb_1"]),
    K("MI_B_1", "ᴹᴵᴰᴵ\nB₁", "Midi send note B₁"),

    K("MI_C_2", "ᴹᴵᴰᴵ\nC₂", "Midi send note C₂"),
    K("MI_Cs_2", "ᴹᴵᴰᴵ\nC#₂/Dᵇ₂", "Midi send note C#₂/Dᵇ₂", alias=["MI_Db_2"]),
    K("MI_D_2", "ᴹᴵᴰᴵ\nD₂", "Midi send note D₂"),
    K("MI_Ds_2", "ᴹᴵᴰᴵ\nD#₂/Eᵇ₂", "Midi send note D#₂/Eᵇ₂", alias=["MI_Eb_2"]),
    K("MI_E_2", "ᴹᴵᴰᴵ\nE₂", "Midi send note E₂"),
    K("MI_F_2", "ᴹᴵᴰᴵ\nF₂", "Midi send note F₂"),
    K("MI_Fs_2", "ᴹᴵᴰᴵ\nF#₂/Gᵇ₂", "Midi send note F#₂/Gᵇ₂", alias=["MI_Gb_2"]),
    K("MI_G_2", "ᴹᴵᴰᴵ\nG₂", "Midi send note G₂"),
    K("MI_Gs_2", "ᴹᴵᴰᴵ\nG#₂/Aᵇ₂", "Midi send note G#₂/Aᵇ₂", alias=["MI_Ab_2"]),
    K("MI_A_2", "ᴹᴵᴰᴵ\nA₂", "Midi send note A₂"),
    K("MI_As_2", "ᴹᴵᴰᴵ\nA#₂/Bᵇ₂", "Midi send note A#₂/Bᵇ₂", alias=["MI_Bb_2"]),
    K("MI_B_2", "ᴹᴵᴰᴵ\nB₂", "Midi send note B₂"),

    K("MI_C_3", "ᴹᴵᴰᴵ\nC₃", "Midi send note C₃"),
    K("MI_Cs_3", "ᴹᴵᴰᴵ\nC#₃/Dᵇ₃", "Midi send note C#₃/Dᵇ₃", alias=["MI_Db_3"]),
    K("MI_D_3", "ᴹᴵᴰᴵ\nD₃", "Midi send note D₃"),
    K("MI_Ds_3", "ᴹᴵᴰᴵ\nD#₃/Eᵇ₃", "Midi send note D#₃/Eᵇ₃", alias=["MI_Eb_3"]),
    K("MI_E_3", "ᴹᴵᴰᴵ\nE₃", "Midi send note E₃"),
    K("MI_F_3", "ᴹᴵᴰᴵ\nF₃", "Midi send note F₃"),
    K("MI_Fs_3", "ᴹᴵᴰᴵ\nF#₃/Gᵇ₃", "Midi send note F#₃/Gᵇ₃", alias=["MI_Gb_3"]),
    K("MI_G_3", "ᴹᴵᴰᴵ\nG₃", "Midi send note G₃"),
    K("MI_Gs_3", "ᴹᴵᴰᴵ\nG#₃/Aᵇ₃", "Midi send note G#₃/Aᵇ₃", alias=["MI_Ab_3"]),
    K("MI_A_3", "ᴹᴵᴰᴵ\nA₃", "Midi send note A₃"),
    K("MI_As_3", "ᴹᴵᴰᴵ\nA#₃/Bᵇ₃", "Midi send note A#₃/Bᵇ₃", alias=["MI_Bb_3"]),
    K("MI_B_3", "ᴹᴵᴰᴵ\nB₃", "Midi send note B₃"),

    K("MI_C_4", "ᴹᴵᴰᴵ\nC₄", "Midi send note C₄"),
    K("MI_Cs_4", "ᴹᴵᴰᴵ\nC#₄/Dᵇ₄", "Midi send note C#₄/Dᵇ₄", alias=["MI_Db_4"]),
    K("MI_D_4", "ᴹᴵᴰᴵ\nD₄", "Midi send note D₄"),
    K("MI_Ds_4", "ᴹᴵᴰᴵ\nD#₄/Eᵇ₄", "Midi send note D#₄/Eᵇ₄", alias=["MI_Eb_4"]),
    K("MI_E_4", "ᴹᴵᴰᴵ\nE₄", "Midi send note E₄"),
    K("MI_F_4", "ᴹᴵᴰᴵ\nF₄", "Midi send note F₄"),
    K("MI_Fs_4", "ᴹᴵᴰᴵ\nF#₄/Gᵇ₄", "Midi send note F#₄/Gᵇ₄", alias=["MI_Gb_4"]),
    K("MI_G_4", "ᴹᴵᴰᴵ\nG₄", "Midi send note G₄"),
    K("MI_Gs_4", "ᴹᴵᴰᴵ\nG#₄/Aᵇ₄", "Midi send note G#₄/Aᵇ₄", alias=["MI_Ab_4"]),
    K("MI_A_4", "ᴹᴵᴰᴵ\nA₄", "Midi send note A₄"),
    K("MI_As_4", "ᴹᴵᴰᴵ\nA#₄/Bᵇ₄", "Midi send note A#₄/Bᵇ₄", alias=["MI_Bb_4"]),
    K("MI_B_4", "ᴹᴵᴰᴵ\nB₄", "Midi send note B₄"),

    K("MI_C_5", "ᴹᴵᴰᴵ\nC₅", "Midi send note C₅"),
    K("MI_Cs_5", "ᴹᴵᴰᴵ\nC#₅/Dᵇ₅", "Midi send note C#₅/Dᵇ₅", alias=["MI_Db_5"]),
    K("MI_D_5", "ᴹᴵᴰᴵ\nD₅", "Midi send note D₅"),
    K("MI_Ds_5", "ᴹᴵᴰᴵ\nD#₅/Eᵇ₅", "Midi send note D#₅/Eᵇ₅", alias=["MI_Eb_5"]),
    K("MI_E_5", "ᴹᴵᴰᴵ\nE₅", "Midi send note E₅"),
    K("MI_F_5", "ᴹᴵᴰᴵ\nF₅", "Midi send note F₅"),
    K("MI_Fs_5", "ᴹᴵᴰᴵ\nF#₅/Gᵇ₅", "Midi send note F#₅/Gᵇ₅", alias=["MI_Gb_5"]),
    K("MI_G_5", "ᴹᴵᴰᴵ\nG₅", "Midi send note G₅"),
    K("MI_Gs_5", "ᴹᴵᴰᴵ\nG#₅/Aᵇ₅", "Midi send note G#₅/Aᵇ₅", alias=["MI_Ab_5"]),
    K("MI_A_5", "ᴹᴵᴰᴵ\nA₅", "Midi send note A₅"),
    K("MI_As_5", "ᴹᴵᴰᴵ\nA#₅/Bᵇ₅", "Midi send note A#₅/Bᵇ₅", alias=["MI_Bb_5"]),
    K("MI_B_5", "ᴹᴵᴰᴵ\nB₅", "Midi send note B₅"),

    K("MI_ALLOFF", "ᴹᴵᴰᴵ\nNotesᵒᶠᶠ", "Midi send all notes OFF"),
]

KEYCODES_MIDI_ADVANCED = [
    K("MI_OCT_N2", "ᴹᴵᴰᴵ\nOct₋₂", "Midi set octave to -2"),
    K("MI_OCT_N1", "ᴹᴵᴰᴵ\nOct₋₁", "Midi set octave to -1"),
    K("MI_OCT_0", "ᴹᴵᴰᴵ\nOct₀", "Midi set octave to 0"),
    K("MI_OCT_1", "ᴹᴵᴰᴵ\nOct₊₁", "Midi set octave to 1"),
    K("MI_OCT_2", "ᴹᴵᴰᴵ\nOct₊₂", "Midi set octave to 2"),
    K("MI_OCT_3", "ᴹᴵᴰᴵ\nOct₊₃", "Midi set octave to 3"),
    K("MI_OCT_4", "ᴹᴵᴰᴵ\nOct₊₄", "Midi set octave to 4"),
    K("MI_OCT_5", "ᴹᴵᴰᴵ\nOct₊₅", "Midi set octave to 5"),
    K("MI_OCT_6", "ᴹᴵᴰᴵ\nOct₊₆", "Midi set octave to 6"),
    K("MI_OCT_7", "ᴹᴵᴰᴵ\nOct₊₇", "Midi set octave to 7"),
    K("MI_OCTD", "ᴹᴵᴰᴵ\nOctᴰᴺ", "Midi move down an octave"),
    K("MI_OCTU", "ᴹᴵᴰᴵ\nOctᵁᴾ", "Midi move up an octave"),

    K("MI_TRNS_N6", "ᴹᴵᴰᴵ\nTrans₋₆", "Midi set transposition to -4 semitones"),
    K("MI_TRNS_N5", "ᴹᴵᴰᴵ\nTrans₋₅", "Midi set transposition to -5 semitones"),
    K("MI_TRNS_N4", "ᴹᴵᴰᴵ\nTrans₋₄", "Midi set transposition to -4 semitones"),
    K("MI_TRNS_N3", "ᴹᴵᴰᴵ\nTrans₋₃", "Midi set transposition to -3 semitones"),
    K("MI_TRNS_N2", "ᴹᴵᴰᴵ\nTrans₋₂", "Midi set transposition to -2 semitones"),
    K("MI_TRNS_N1", "ᴹᴵᴰᴵ\nTrans₋₁", "Midi set transposition to -1 semitones"),
    K("MI_TRNS_0", "ᴹᴵᴰᴵ\nTrans₀", "Midi set no transposition"),
    K("MI_TRNS_1", "ᴹᴵᴰᴵ\nTrans₊₁", "Midi set transposition to +1 semitones"),
    K("MI_TRNS_2", "ᴹᴵᴰᴵ\nTrans₊₂", "Midi set transposition to +2 semitones"),
    K("MI_TRNS_3", "ᴹᴵᴰᴵ\nTrans₊₃", "Midi set transposition to +3 semitones"),
    K("MI_TRNS_4", "ᴹᴵᴰᴵ\nTrans₊₄", "Midi set transposition to +4 semitones"),
    K("MI_TRNS_5", "ᴹᴵᴰᴵ\nTrans₊₅", "Midi set transposition to +5 semitones"),
    K("MI_TRNS_6", "ᴹᴵᴰᴵ\nTrans₊₆", "Midi set transposition to +6 semitones"),
    K("MI_TRNSD", "ᴹᴵᴰᴵ\nTransᴰᴺ", "Midi decrease transposition"),
    K("MI_TRNSU", "ᴹᴵᴰᴵ\nTransᵁᴾ", "Midi increase transposition"),

    K("MI_VEL_1", "ᴹᴵᴰᴵ\nVel₁", "Midi set velocity to 0", alias=["MI_VEL_0"]),
    K("MI_VEL_2", "ᴹᴵᴰᴵ\nVel₂", "Midi set velocity to 25"),
    K("MI_VEL_3", "ᴹᴵᴰᴵ\nVel₃", "Midi set velocity to 38"),
    K("MI_VEL_4", "ᴹᴵᴰᴵ\nVel₄", "Midi set velocity to 51"),
    K("MI_VEL_5", "ᴹᴵᴰᴵ\nVel₅", "Midi set velocity to 64"),
    K("MI_VEL_6", "ᴹᴵᴰᴵ\nVel₆", "Midi set velocity to 76"),
    K("MI_VEL_7", "ᴹᴵᴰᴵ\nVel₇", "Midi set velocity to 89"),
    K("MI_VEL_8", "ᴹᴵᴰᴵ\nVel₈", "Midi set velocity to 102"),
    K("MI_VEL_9", "ᴹᴵᴰᴵ\nVel₉", "Midi set velocity to 114"),
    K("MI_VEL_10", "ᴹᴵᴰᴵ\nVel₁₀", "Midi set velocity to 127"),
    K("MI_VELD", "ᴹᴵᴰᴵ\nVelᴰᴺ", "Midi decrease velocity"),
    K("MI_VELU", "ᴹᴵᴰᴵ\nVelᵁᴾ", "Midi increase velocity"),

    K("MI_CH1", "ᴹᴵᴰᴵ\nCH₁", "Midi set channel to 1"),
    K("MI_CH2", "ᴹᴵᴰᴵ\nCH₂", "Midi set channel to 2"),
    K("MI_CH3", "ᴹᴵᴰᴵ\nCH₃", "Midi set channel to 3"),
    K("MI_CH4", "ᴹᴵᴰᴵ\nCH₄", "Midi set channel to 4"),
    K("MI_CH5", "ᴹᴵᴰᴵ\nCH₅", "Midi set channel to 5"),
    K("MI_CH6", "ᴹᴵᴰᴵ\nCH₆", "Midi set channel to 6"),
    K("MI_CH7", "ᴹᴵᴰᴵ\nCH₇", "Midi set channel to 7"),
    K("MI_CH8", "ᴹᴵᴰᴵ\nCH₈", "Midi set channel to 8"),
    K("MI_CH9", "ᴹᴵᴰᴵ\nCH₉", "Midi set channel to 9"),
    K("MI_CH10", "ᴹᴵᴰᴵ\nCH₁₀", "Midi set channel to 10"),
    K("MI_CH11", "ᴹᴵᴰᴵ\nCH₁₁", "Midi set channel to 11"),
    K("MI_CH12", "ᴹᴵᴰᴵ\nCH₁₂", "Midi set channel to 12"),
    K("MI_CH13", "ᴹᴵᴰᴵ\nCH₁₃", "Midi set channel to 13"),
    K("MI_CH14", "ᴹᴵᴰᴵ\nCH₁₄", "Midi set channel to 14"),
    K("MI_CH15", "ᴹᴵᴰᴵ\nCH₁₅", "Midi set channel to 15"),
    K("MI_CH16", "ᴹᴵᴰᴵ\nCH₁₆", "Midi set channel to 16"),
    K("MI_CHD", "ᴹᴵᴰᴵ\nCHᴰᴺ", "Midi decrease channel"),
    K("MI_CHU", "ᴹᴵᴰᴵ\nCHᵁᴾ", "Midi increase channel"),

    K("MI_SUS", "ᴹᴵᴰᴵ\nSust", "Midi Sustain"),
    K("MI_PORT", "ᴹᴵᴰᴵ\nPort", "Midi Portmento"),
    K("MI_SOST", "ᴹᴵᴰᴵ\nSost", "Midi Sostenuto"),
    K("MI_SOFT", "ᴹᴵᴰᴵ\nSPedal", "Midi Soft Pedal"),
    K("MI_LEG", "ᴹᴵᴰᴵ\nLegat", "Midi Legato"),
    K("MI_MOD", "ᴹᴵᴰᴵ\nModul", "Midi Modulation"),
    K("MI_MODSD", "ᴹᴵᴰᴵ\nModulᴰᴺ", "Midi decrease modulation speed"),
    K("MI_MODSU", "ᴹᴵᴰᴵ\nModulᵁᴾ", "Midi increase modulation speed"),
    K("MI_BENDD", "ᴹᴵᴰᴵ\nBendᴰᴺ", "Midi bend pitch down"),
    K("MI_BENDU", "ᴹᴵᴰᴵ\nBendᵁᴾ", "Midi bend pitch up"),
]

KEYCODES_HIDDEN = []
for x in range(256):
    KEYCODES_HIDDEN.append(K("TD({})".format(x), "TD({})".format(x)))

KEYCODES = []
KEYCODES_MAP = dict()
RAWCODES_MAP = dict()

K = None


def recreate_keycodes():
    """ Regenerates global KEYCODES array """

    KEYCODES.clear()
    KEYCODES.extend(KEYCODES_SPECIAL + KEYCODES_BASIC + KEYCODES_SHIFTED + KEYCODES_ISO + KEYCODES_LAYERS +
                    KEYCODES_BOOT + KEYCODES_MODIFIERS + KEYCODES_QUANTUM + KEYCODES_BACKLIGHT + KEYCODES_MEDIA +
                    KEYCODES_TAP_DANCE + KEYCODES_MACRO + KEYCODES_USER + KEYCODES_HIDDEN + KEYCODES_MIDI)
    KEYCODES_MAP.clear()
    RAWCODES_MAP.clear()
    for keycode in KEYCODES:
        KEYCODES_MAP[keycode.qmk_id.replace("(kc)", "")] = keycode
        RAWCODES_MAP[Keycode.deserialize(keycode.qmk_id)] = keycode


def create_user_keycodes():
    KEYCODES_USER.clear()
    for x in range(16):
        KEYCODES_USER.append(
            Keycode(
                "USER{:02}".format(x),
                "User {}".format(x),
                "User keycode {}".format(x)
            )
        )


def create_custom_user_keycodes(custom_keycodes):
    KEYCODES_USER.clear()
    for x, c_keycode in enumerate(custom_keycodes):
        KEYCODES_USER.append(
            Keycode(
                "USER{:02}".format(x),
                c_keycode.get("shortName", "USER{:02}".format(x)),
                c_keycode.get("title", "USER{:02}".format(x)),
                alias=[c_keycode.get("name", "USER{:02}".format(x))]
            )
        )


def create_midi_keycodes(midiSettingLevel):
    KEYCODES_MIDI.clear()

    if midiSettingLevel == "basic" or midiSettingLevel == "advanced":
        KEYCODES_MIDI.extend(KEYCODES_MIDI_BASIC)

    if midiSettingLevel == "advanced":
        KEYCODES_MIDI.extend(KEYCODES_MIDI_ADVANCED)


def recreate_keyboard_keycodes(keyboard):
    """ Generates keycodes based on information the keyboard provides (e.g. layer keycodes, macros) """

    Keycode.protocol = keyboard.vial_protocol

    layers = keyboard.layers

    def generate_keycodes_for_mask(label, description):
        keycodes = []
        for layer in range(layers):
            lbl = "{}({})".format(label, layer)
            keycodes.append(Keycode(lbl, lbl, description))
        return keycodes

    KEYCODES_LAYERS.clear()

    if layers >= 4:
        KEYCODES_LAYERS.append(Keycode("FN_MO13", "Fn1\n(Fn3)"))
        KEYCODES_LAYERS.append(Keycode("FN_MO23", "Fn2\n(Fn3)"))

    KEYCODES_LAYERS.extend(
        generate_keycodes_for_mask("MO",
                                   "按下时暂时切换到该层(松开恢复到默认层)"))
    KEYCODES_LAYERS.extend(
        generate_keycodes_for_mask("DF",
                                   "设置该层为基础（默认）层"))
    KEYCODES_LAYERS.extend(
        generate_keycodes_for_mask("TG",
                                   "切换到该层或者切回默认层"))
    KEYCODES_LAYERS.extend(
        generate_keycodes_for_mask("TT",
                                   "按下时暂时切换到该层，连续点击多次后，切换到该层，再连续点击多次后，切回默认层"))
    KEYCODES_LAYERS.extend(
        generate_keycodes_for_mask("OSL",
                                   "暂时切换到该层，按下下一个键后，切回默认层"))
    KEYCODES_LAYERS.extend(
        generate_keycodes_for_mask("TO",
                                   "切换到该层"))

    for x in range(min(layers, 16)):
        KEYCODES_LAYERS.append(Keycode("LT{}(kc)".format(x), "LT {}\n(kc)".format(x),
                                       "单击触发键值，长按切换到层 {} ".format(x), masked=True))

    KEYCODES_MACRO.clear()
    for x in range(keyboard.macro_count):
        lbl = "M{}".format(x)
        KEYCODES_MACRO.append(Keycode(lbl, lbl))

    for x, kc in enumerate(KEYCODES_MACRO_BASE):
        KEYCODES_MACRO.append(kc)

    KEYCODES_TAP_DANCE.clear()
    for x in range(keyboard.tap_dance_count):
        lbl = "TD({})".format(x)
        KEYCODES_TAP_DANCE.append(Keycode(lbl, lbl, "Tap dance keycode"))

    # Check if custom keycodes are defined in keyboard, and if so add them to user keycodes
    if keyboard.custom_keycodes is not None and len(keyboard.custom_keycodes) > 0:
        create_custom_user_keycodes(keyboard.custom_keycodes)
    else:
        create_user_keycodes()

    create_midi_keycodes(keyboard.midi)

    recreate_keycodes()


recreate_keycodes()
