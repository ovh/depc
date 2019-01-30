QOS_PER_TEAM = """
[ $token 'depc.qos.label' { 'team' '$TEAM$' } $start $end ] FETCH
{  '.app' '' } RELABEL
INTERPOLATE
"""

QOS_FILTERED_BY_LABEL = """
[ $token 'depc.qos.label' { 'team' '$TEAM$' 'name' '$NAME$' } $start $end ] FETCH
{  '.app' '' } RELABEL
INTERPOLATE
"""

# Specific item QOS
QOS_ITEM_PER_TEAM_LABEL = """
[   $token
    'depc.qos.node'
    { 'team' '$TEAM$' 'label' '$LABEL$' 'name' '$NAME$' }
    $start $end
] FETCH

{  '.app' '' } RELABEL
"""

# Get the statistics per team
STATISTICS_SCRIPT = """
[   $token
    'depc.qos.stats'
    { 'team' '$TEAM$' $FILTER$ }
    $start $end
] FETCH

{  '.app' '' } RELABEL
"""

# Worst items per label
QOS_WORST_ITEM_PER_LABEL = """
$COUNT$ 'topN' STORE
$topN 1 - 'topN' STORE

[   $token
    'depc.qos.node'
    { 'team' '$TEAM$' 'label' '$LABEL$' }
    $start $end
] FETCH

// remove useless DATA
{  '.app' '' 'label' '' } RELABEL

// compute mean value over the whole timespan
[ SWAP bucketizer.mean 0 0 1 ] BUCKETIZE

// sort the GTS (based on their latest value)
LASTSORT

// return results if any, else an empty stack []
DUP
SIZE 'topSize' STORE

<% $topSize 0 > %>
<% [ 0 $topN ] SUBLIST %>
IFT
"""
