# MacBook battery — 7 settings

Shipped gold. Posted copy. conversation `2102172499031253210`.

Beat labels are structure, not lines to copy. Wording is what shipped. Card jokes and unsourced figures stay in this file. Promoted rules live in `.grok/skills/hidden-settings/SKILL.md`.

<!-- neglect -->
Most MacBooks get unboxed, signed into iCloud, and then never opened past Wi-Fi and display brightness.

<!-- scene -->
Someone charged to 100% before a workday. By 3pm the machine was dead in a cafe, still mid-document. They were one click away from booking Apple’s battery replacement.

<!-- expert -->
A friend who repairs Macs for a living sat down, opened System Settings, and spent 8 minutes in menus most owners never touch.

<!-- no-list -->
– Didn’t replace the battery
– Didn’t buy a new charger
– Didn’t install a “cleaner” app

<!-- snap -->
He changed 7 settings.

Same MacBook lasted into the evening on the next charge.

<!-- thesis -->
“Your battery was never as dead as it looked. macOS ships with a pile of background jobs left on — sleep that isn’t sleep, apps that launch themselves, indexing that never clocks off. Apple will sell you a new battery. They will not walk you through the free pass first.”

<!-- promise -->
🧵 Here are the 7 settings that fixed it:

---

<!-- card 1 -->
Setting 1: Low Power Mode on battery only

macOS defaults to Automatic. Fine on paper. In practice the machine keeps doing background work while you’re unplugged and wondering why 80% became 40% before lunch.

Apple menu → System Settings → Battery

Set Low Power Mode to Only on Battery.

On some versions this sits under Energy Mode → On battery → Low Power.

Leave it off (or Automatic) when the charger is in. You want the saving when you’re walking around, not when you’re at a desk.

This is the one-toggle version of “stop sprinting between meetings.”

<!-- card 2 -->
Setting 2: Wake for network access

Your MacBook can wake itself from sleep to check mail, iCloud, and shared folders. Then it goes back to sleep. Then it wakes again.

That is how a lid-closed machine loses 20–30% overnight in a bag.

System Settings → Battery → Options

Wake for network access → Never

or Only on Power Adapter if you actually share files from this laptop.

If you needed the laptop reachable on the network while it sleeps, you would already know. Most people do not.

This is the “why is my battery lower this morning than last night” setting.

<!-- card 3 -->
Setting 3: Power Nap off

Power Nap is Apple’s name for “keep doing work while you think this thing is asleep.” Mail. Time Machine. iCloud. Updates.

Useful on a desktop that sits on a desk. Less useful on a laptop that lives in a backpack.

System Settings → Battery → Options

Enable Power Nap → Off

You still get updates when you open the lid. You just stop paying for them at 2am.

<!-- card 4 -->
Setting 4: Login Items and background apps

Open the lid and 15 helpers wake up with you. Dropbox. Adobe. Teams. Spotify. A Google updater for a browser you used twice in 2024.

None of them ask. They just sit there.

System Settings → General → Login Items & Extensions

Check both lists:

– Open at Login
– Allow in the Background

Turn off anything you do not use every day. Keep iCloud extras you actually need. Kill the rest.

If you are not sure what something is, search the name before you toggle it. Then toggle it.

This is often the difference between a 20-second wake and a 2-minute fan spin.

<!-- card 5 -->
Setting 5: Activity Monitor, Energy tab

Settings can only catch what Apple labelled. The real drain is usually one app you left open.

Command + Space → type Activity Monitor → open it → click Energy

Sort by Energy Impact.

The top one or two rows are the story. Chrome with 40 tabs. Slack. A Zoom helper from a call that ended an hour ago. Photos stuck uploading.

Quit those. Then look at 12 hr Power if you want the longer picture.

Do this once this week. You will find the culprit in under a minute.

<!-- card 6 -->
Setting 6: Pause iCloud Photos on battery

iCloud Photos will happily chew a charge uploading original-size images over cafe Wi-Fi. On a slow connection it can flatten a battery before you finish lunch.

Open Photos → Settings → iCloud

Pause for a day when you are out. Resume when you are back on power and decent Wi-Fi.

Also worth it: System Settings → Displays → brightness around the middle, auto-brightness on. The screen is still the biggest hardware drain on the machine. This is not clever. It just works.

⚠️ If you do not use iCloud Photos, skip the pause and only do brightness.

<!-- card 7 -->
Setting 7: Stop Spotlight indexing the whole disk

After an OS update, Spotlight can reindex for hours and sit on the CPU while you work. On older machines it feels like the laptop is sick.

System Settings → Spotlight

Uncheck result categories you never search (fonts, web, Siri suggestions if you do not use them).

Then open Search Privacy and add folders that do not need to be indexed — old archive drives, VM images, node_modules dumps, Time Machine leftovers.

You can still find your files. Spotlight just stops crawling junk all day.

If Activity Monitor showed mds or mds_stores near the top, this was the card you needed.

---

<!-- closer -->
The full pass.

✓ Low Power Mode on battery only
✓ Wake for network access off
✓ Power Nap off
✓ Login Items cleaned
✓ Energy tab checked
✓ iCloud Photos paused when out
✓ Spotlight privacy trimmed

Same MacBook. Same battery. Different day.

Eight minutes. $0. No replacement. No “cleaner” app.

Apple will quote you a few hundred dollars to swap a battery that still had hours left in it. The hours were going to background jobs you never asked for.

Save this before you book the battery replacement.

<!-- cta -->
Reply with Intel or Apple Silicon + roughly how old the machine is, and I’ll tell you which 3 of these 7 move the needle first.
