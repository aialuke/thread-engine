# Sources

Checked: 2026-09-22
Models: 2024–2026 4K TVs, AU. Samsung Tizen, LG webOS 22–26, Sony Google TV / BRAVIA, Hisense VIDAA.

Unconfirmed (VERIFY, cut from cards): LG Live Plus path, Sony Samba Interactive TV, Hisense HDMI format, Hisense Google TV / Roku motion labels, Sharpness “set to 0”.

Scene money: JB Hi-Fi Samsung 65" S90H OLED [2026] $3,244 on 2026-09-22. https://www.jbhifi.com.au/collections/deals-on-tvs-and-soundbars

## Setting 1: Motion Off

- Path (Samsung): Settings → Picture → Expert Settings → Auto Motion Plus Settings (Picture Clarity Settings) → Off
- URL: https://www.samsung.com/us/support/answer/ANS10006969/
- Retrieved: 2026-09-22
- Models: Samsung Tizen 2024–2026; default Auto
- Skip if: no motion menu, or sport night (put Auto/Custom back)

- Path (LG): All Settings → Picture → Advanced Settings → Clarity → TruMotion → Off
- URL: https://www.lg.com/us/support/help-library/lg-tv-troubleshooting-poor-picture-quailty-on-ps5--20153303206885
- Retrieved: 2026-09-22
- Models: webOS 6.0 / 22+; webOS 5.0 fork is Picture Mode Settings → Picture Option → TruMotion
- Skip if: Game Optimizer (TruMotion hidden)

- Path (Sony): Settings → Display & Sound → Picture → Motion → Motionflow → Off
- URL: https://helpguide.sony.net/tv/jusltn1/v1/en-003/01-03-09_01.html
- Retrieved: 2026-09-22
- Models: BRAVIA Google TV
- Skip if: no Motionflow row

- Path (Hisense VIDAA): Settings → Picture → Picture Mode Settings → Motion → Ultra Smooth Motion → Off
- URL: https://www.hisense.com.my/wp-content/uploads/2025/07/B_92707_9655_U901_EUAUCO_E-Manual_pdf_large_UK-eng_20250416.pdf
- Retrieved: 2026-09-22
- Models: VIDAA 2025 e-manual
- Skip if: not VIDAA (Google TV / Roku labels VERIFY)

## Setting 2: Picture mode

- Path (Samsung): Settings → All Settings → Picture → Picture Mode → FILMMAKER MODE (fallback Movie); Apply Picture Settings → all sources
- URL: https://www.samsung.com/us/support/answer/ANS10006970/
- Retrieved: 2026-09-22
- Models: Tizen with FILMMAKER MODE; Standard is official default
- Skip if: no Filmmaker / Movie row

- Path (LG): All Settings → Picture → Select Mode → FILMMAKER MODE (fallback Cinema); FILMMAKER MODE Auto Start → On
- URL: https://www.lg.com/us/support/help-library/how-to-fix-a-dark-or-dim-picture-on-your-lg-tv--20155311256311
- Retrieved: 2026-09-22
- Models: webOS 6+
- Skip if: no Filmmaker / Cinema row

- Path (Sony): Settings → Display & Sound → Picture → Picture mode → Cinema (Professional on some 2024+)
- URL: https://helpguide.sony.net/tv/jusltn1/v1/en-003/01-03-09_01.html
- Retrieved: 2026-09-22
- Models: BRAVIA. No Filmmaker Mode on official helpguide
- Skip if: no Cinema / Professional row

- Path (Hisense VIDAA): Settings → Picture → Picture Mode → FILMMAKER or Cinema
- URL: https://www.hisense.com.my/wp-content/uploads/2025/07/B_92707_9655_U901_EUAUCO_E-Manual_pdf_large_UK-eng_20250416.pdf
- Retrieved: 2026-09-22
- Models: VIDAA; auto-switch only when tagged
- Skip if: no FILMMAKER / Cinema row

UHD Alliance (what FMM disables): https://filmmakermode.com/about/

## Setting 3: Energy saving Off

- Path (Samsung AU 2025): Settings → All Settings → General & Privacy → Power and Energy Saving → Energy Saving Solution / Brightness Optimisation / Motion Lighting Off
- URL: https://www.samsung.com/au/support/tv-audio-video/reduce-energy-consumption-of-your-smart-tv/
- Retrieved: 2026-09-22
- Models: 2025 AU; 2024 fork via Support → Device Care
- Skip if: no Power and Energy Saving row

- Path (LG): All Settings → General → Energy Saving → Energy Saving Step → Off (webOS 26: System → Energy Saving)
- URL: https://www.lg.com/us/support/help-library/how-to-fix-a-dark-or-dim-picture-on-your-lg-tv--20155311256311
- Retrieved: 2026-09-22
- Models: webOS 22–26
- Skip if: no Energy Saving Step

- Path (Sony): Display & Sound → Picture → Light sensor / Ambient light sensor → Off
- URL: https://helpguide.sony.net/tv/jusltn1/v1/en-003/01-03-09_01.html
- Retrieved: 2026-09-22
- Models: BRAVIA; Eco Dashboard on newer firmware
- Skip if: no light sensor

- Path (Hisense VIDAA): leave Picture Mode off Energy Saving; Automatic Light Sensor Off; AI Energy mode Off
- URL: https://www.hisense.com.my/wp-content/uploads/2025/07/B_92707_9655_U901_EUAUCO_E-Manual_pdf_large_UK-eng_20250416.pdf
- Retrieved: 2026-09-22
- Models: VIDAA
- Skip if: no sensor / Energy Saving mode

## Setting 4: Sharpness down

- Path (Samsung): All Settings → Picture → Expert Settings → Sharpness
- URL: https://www.samsung.com/us/support/answer/ANS10006970/
- Retrieved: 2026-09-22
- Models: Tizen Expert Settings
- Skip if: already FILMMAKER MODE, or no Sharpness slider

- Path (LG): All Settings → Picture (Picture Mode Settings) → Sharpness
- URL: https://www.lg.com/us/support/help-library/lg-tv-the-best-picture-settings-for-your-lg-tv--20150577528034
- Retrieved: 2026-09-22
- Models: webOS
- Skip if: FILMMAKER MODE

- Path (Sony): Display & Sound → Picture → Clarity
- URL: https://helpguide.sony.net/tv/jusltn1/v1/en-003/01-03-09_01.html
- Retrieved: 2026-09-22
- Models: BRAVIA
- Skip if: no Clarity row

- Path (Hisense VIDAA): Picture Mode Settings → Sharpness
- URL: https://www.hisense.com.my/wp-content/uploads/2025/07/B_92707_9655_U901_EUAUCO_E-Manual_pdf_large_UK-eng_20250416.pdf
- Retrieved: 2026-09-22
- Models: VIDAA
- Skip if: FILMMAKER MODE

## Setting 5: Colour tone Warm

- Path (Samsung): Expert Settings → Color Tone → Warm2
- URL: https://www.samsung.com/us/support/answer/ANS10006970/
- Retrieved: 2026-09-22
- Models: Tizen
- Skip if: already FILMMAKER MODE

- Path (LG): Picture → Advanced Settings → Color → Color Temperature → Warm
- URL: http://kr.eguide.lgappstv.com/manual/w25/w25_t46/engb.html
- Retrieved: 2026-09-22
- Models: webOS 25 e-guide; Warm vs Warm50 varies
- Skip if: FILMMAKER MODE

- Path (Sony): Picture → Adv. color temperature
- URL: https://helpguide.sony.net/tv/jusltn1/v1/en-003/01-03-09_01.html
- Retrieved: 2026-09-22
- Models: BRAVIA
- Skip if: Cinema already looks right

- Path (Hisense): Picture Mode Settings → Colour / colour temperature
- URL: https://www.hisense.com.my/wp-content/uploads/2025/07/B_92707_9655_U901_EUAUCO_E-Manual_pdf_large_UK-eng_20250416.pdf
- Retrieved: 2026-09-22
- Models: VIDAA
- Skip if: FILMMAKER MODE

## Setting 6: HDMI enhanced

- Path (Samsung): All Settings → General & Privacy → External Device Manager → Input Signal Plus → HDMI port On (older name HDMI UHD Color)
- URL: https://downloadcenter.samsung.com/content/PM/202507/20250728135454825/EN/ENG/ENG/1_tv-guide_6.html
- Retrieved: 2026-09-22
- Models: 2025 Tizen user guide
- Skip if: no HDMI box (built-in Netflix / YouTube / iView only)

- Path (Sony): Settings → Channels & Inputs → External inputs → HDMI signal format → Enhanced format
- URL: https://helpguide.sony.net/tv/iusltn1/v1/en-003/print.html
- Retrieved: 2026-09-22
- Models: BRAVIA; 4K120/VRR on labelled ports
- Skip if: no HDMI box

- Path (LG): All Settings → Picture → Additional Settings → HDMI Ultra HD Deep Color → On for the 4K port
- URL: https://www.lg.com/us/support/help-library/lg-tv-how-to-perform-a-picture-test--20153275651659
- Retrieved: 2026-09-22
- Models: webOS; Off for HD-or-lower boxes
- Skip if: no HDMI box

- Path (Hisense): VERIFY — cut from a fake universal path
- Skip if: Hisense, or no HDMI box

## Setting 7: Viewing information

- Path (Samsung): Privacy Choices app or Settings → turn off Viewing Information Services (and Customised Ads / Interest-Based Advertising if shown)
- URL: https://www.samsung.com/us/support/answer/ANS10010616/
- Retrieved: 2026-09-22
- Also: https://www.samsung.com/au/info/ads-privacy/
- Models: Samsung Smart TV ACR / Viewing Information Services
- Skip if: label missing

- Path (Google TV: Sony, some Hisense): Settings → Privacy → Ads → Delete advertising ID
- URL: https://support.google.com/googletv/answer/13392198?hl=en
- Retrieved: 2026-09-22
- Models: Google TV. Ads cannot be turned off; delete the ID
- Skip if: not Google TV

- Path (LG Live Plus): VERIFY — cut from numbered posts
- Skip if: LG
